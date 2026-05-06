import logging
from typing import Dict, Any
from app.models.driver_model import DriverModel
from app.models.user_model import UserModel

class DriverController:
    """Processes business logic and formats data for Driver Management."""

    def __init__(self) -> None:
        """Initializes the model and creates the table."""
        self.model = DriverModel()
        self.model.create_table()
        self.user_model = UserModel()

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

    def add_new_driver(self, d_id: str, first_name: str, last_name: str, status: str, licenses: str, exp: str, dob: str, address: str, avail: str, username: str = None, password: str = None) -> dict:
        """Handles logic for adding a new driver and automatically creates an account."""
        
        full_name = f"{first_name} {last_name}".strip()
        
        if username and password:
            account_created = self.user_model.register_user(
                username=username, 
                password=password, 
                first_name=first_name, 
                last_name=last_name,
                email=None, 
                phone_number=None,
                date_of_birth=dob,
                role="Driver",
                address=address
            )
            
            if not account_created:
                return {"success": False, "message": f"Error: The username '{username}' is already taken."}

        result = self.model.insert_driver(d_id, full_name, status, licenses, exp, dob, address, avail)
        
        if result is True:
            return {"success": True, "message": f"Driver {full_name} added successfully!"}
        else:
            return {"success": False, "message": "Error: Driver ID or Data might already exist."}

    def modify_driver(self, d_id: str, first_name: str, last_name: str, status: str, licenses: str, exp: str, dob: str, address: str, avail: str) -> dict:
        """Handles logic for updating a driver."""
        full_name = f"{first_name} {last_name}".strip()
        result = self.model.update_driver(d_id, full_name, status, licenses, exp, dob, address, avail)
        if result is True:
            return {"success": True, "message": f"Driver {full_name} updated successfully!"}
        else:
            return {"success": False, "message": "Error updating driver."}

    def remove_driver(self, d_id: str) -> dict:
        """Handles logic for removing a driver."""
        result = self.model.delete_driver(d_id)
        if result is True:
            return {"success": True, "message": "Driver deleted successfully!"}
        else:
            return {"success": False, "message": "Error deleting driver."}