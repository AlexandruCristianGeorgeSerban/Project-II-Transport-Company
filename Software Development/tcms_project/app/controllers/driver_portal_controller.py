import logging
from typing import Dict, Any
from app.models.driver_portal_model import DriverPortalModel

class DriverPortalController:
    """Processes business logic for the Driver Portal."""

    def __init__(self) -> None:
        self.model = DriverPortalModel()

    def load_dashboard_data(self, driver_id: str) -> Dict[str, Any]:
        """Loads and structures all necessary data for the driver dashboard."""
        dashboard_data: Dict[str, Any] = {}
        try:
            
            dashboard_data["my_jobs"] = self.model.get_jobs_by_driver(driver_id)
            
           
            dashboard_data["my_vehicle"] = self.model.get_assigned_vehicle(driver_id) 
            
            return dashboard_data
        except Exception as logic_error:
            logging.error(f"Error processing driver dashboard data: {logic_error}")
            dashboard_data["my_jobs"] = []
            dashboard_data["my_vehicle"] = None
            return dashboard_data

    def update_job_status(self, job_id: str, new_status: str) -> dict:
        """Actualizează statusul cursei și eliberează mașina/șoferul dacă e finalizată."""
        try:
             import sqlite3
             DB_PATH = "instance/database.sqlite"
             
             with sqlite3.connect(DB_PATH) as connection:
                  db_cursor = connection.cursor()
                  
                 
                  db_cursor.execute("UPDATE transport_requests SET status = ? WHERE id = ?", (new_status, job_id))
                  
                 
                  if new_status == 'Delivered':
                        db_cursor.execute("UPDATE vehicles SET status = 'Available' WHERE id IN (SELECT vehicle_id FROM transport_requests WHERE id = ?)", (job_id,))
                        db_cursor.execute("UPDATE drivers SET status = 'Available', availability = 'Available' WHERE id IN (SELECT driver_id FROM transport_requests WHERE id = ?)", (job_id,))
                  
                  connection.commit()
                  return {"success": True, "message": f"Job status successfully updated to {new_status}!"}
        except Exception as error:
             import logging
             logging.error(f"Error updating job status: {error}")
             return {"success": False, "message": "Could not update the status."}