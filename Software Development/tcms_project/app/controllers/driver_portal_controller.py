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
            # 1. Preluăm cursele alocate acestui șofer
            dashboard_data["my_jobs"] = self.model.get_jobs_by_driver(driver_id)
            
            # 2. Preluăm vehiculul alocat (din prima cursă activă găsită)
            dashboard_data["my_vehicle"] = self.model.get_assigned_vehicle(driver_id) 
            
            return dashboard_data
        except Exception as logic_error:
            logging.error(f"Error processing driver dashboard data: {logic_error}")
            dashboard_data["my_jobs"] = []
            dashboard_data["my_vehicle"] = None
            return dashboard_data

    def update_job_status(self, job_id: str, new_status: str) -> dict:
        """Handles logic for updating the status of a job."""
        try:
            result = self.model.update_job_status(job_id, new_status)
            if result:
                return {"success": True, "message": f"Job status updated to {new_status}!"}
            else:
                return {"success": False, "message": "Failed to update job status."}
        except Exception as e:
            logging.error(f"Error updating job status: {e}")
            return {"success": False, "message": "An error occurred while updating job status."}