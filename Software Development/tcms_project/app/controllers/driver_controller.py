import logging
from typing import Dict, Any
from app.models.driver_model import DriverModel

class DriverController:
    """Processes business logic and formats data for Driver Management."""

    def __init__(self) -> None:
        """Initializes the model and creates the table."""
        self.model = DriverModel()
        self.model.create_table()

    def load_driver_data(self) -> Dict[str, Any]:
        """Loads and structures all necessary driver data."""
        driver_data: Dict[str, Any] = {}
        try:
            driver_data["summary"] = self.model.get_driver_summary()
            driver_data["drivers"] = self.model.get_all_drivers()
            return driver_data
        except Exception as logic_error:
            logging.error(f"Error processing driver data: {logic_error}")
            driver_data["summary"] = {"total": 0, "active": 0, "on_leave": 0}
            driver_data["drivers"] = []
            return driver_data

    def add_new_driver(self, d_id: str, name: str, status: str, licenses: str, exp: str, dob: str, doc_id: str, address: str, avail: str) -> dict:
        """Handles logic for adding a new driver."""
        result = self.model.insert_driver(d_id, name, status, licenses, exp, dob, doc_id, address, avail)
        if result is True:
            return {"success": True, "message": f"Driver {name} added successfully!"}
        else:
            return {"success": False, "message": "Error: Driver ID might already exist."}

    def modify_driver(self, d_id: str, name: str, status: str, licenses: str, exp: str, dob: str, doc_id: str, address: str, avail: str) -> dict:
        """Handles logic for updating a driver."""
        result = self.model.update_driver(d_id, name, status, licenses, exp, dob, doc_id, address, avail)
        if result is True:
            return {"success": True, "message": f"Driver {name} updated successfully!"}
        else:
            return {"success": False, "message": "Error updating driver."}

    def remove_driver(self, d_id: str) -> dict:
        """Handles logic for removing a driver."""
        result = self.model.delete_driver(d_id)
        if result is True:
            return {"success": True, "message": "Driver deleted successfully!"}
        else:
            return {"success": False, "message": "Error deleting driver."}