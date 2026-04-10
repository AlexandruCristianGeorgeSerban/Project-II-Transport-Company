import logging
from typing import Dict, Any
from app.models.fleet_model import FleetModel

class FleetController:
    """Processes business logic and formats data for the Fleet Management views."""

    def __init__(self) -> None:
        """Initializes the fleet model and ensures the DB table exists."""
        self.model = FleetModel()
        self.model.create_table()

    def load_fleet_data(self) -> Dict[str, Any]:
        """Loads and structures all necessary vehicle data for the UI."""
        fleet_data: Dict[str, Any] = {}

        try:
            fleet_data["summary"] = self.model.get_fleet_summary()
            fleet_data["vehicles"] = self.model.get_all_vehicles()
            return fleet_data
        except Exception as logic_error:
            logging.error(f"Error processing fleet data: {logic_error}")
            fleet_data["summary"] = {"total": 0, "active": 0, "maintenance": 0}
            fleet_data["vehicles"] = []
            return fleet_data

    def add_new_vehicle(self, v_id: str, plate: str, v_type: str, capacity: int, status: str) -> dict:
        """Handles the logic for adding a new vehicle from the user interface."""
        result = self.model.insert_vehicle(v_id, plate, v_type, capacity, status)

        if result is True:
            return {"success": True, "message": f"Vehicle {v_id} added successfully!"}
        else:
            return {"success": False, "message": "Error: Vehicle ID might already exist."}

    def remove_vehicle(self, v_id: str) -> dict:
        """Handles the logic for removing a vehicle."""
        result = self.model.delete_vehicle(v_id)

        if result is True:
            return {"success": True, "message": "Vehicle deleted successfully!"}
        else:
            return {"success": False, "message": "Error deleting vehicle."}

    def modify_vehicle(self, v_id: str, plate: str, v_type: str, capacity: int, status: str) -> dict:
        """Handles the logic for updating an existing vehicle."""
        result = self.model.update_vehicle(v_id, plate, v_type, capacity, status)

        if result is True:
            return {"success": True, "message": f"Vehicle {v_id} updated successfully!"}
        else:
            return {"success": False, "message": "Error updating vehicle."}