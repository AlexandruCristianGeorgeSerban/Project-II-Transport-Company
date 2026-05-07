import logging
from typing import Dict, Any
from app.models.fleet_model import FleetModel
from app.controllers.log_controller import LogController

class FleetController:
    """Processes business logic and formats data for the Fleet Management views."""

    def __init__(self) -> None:
        self.model = FleetModel()
        self.model.create_table()
        self.logger = LogController()

    def load_fleet_data(self) -> Dict[str, Any]:
        fleet_data: Dict[str, Any] = {}
        try:
            fleet_data["summary"] = self.model.get_fleet_summary()
            fleet_data["vehicles"] = self.model.get_all_vehicles()
            return fleet_data
        except Exception as logic_error:
            logging.error(f"Error processing fleet data: {logic_error}")
            return {"summary": {"total": 0, "active": 0, "maintenance": 0}, "vehicles": []}

    def add_new_vehicle(self, v_id: str, plate: str, v_type: str, capacity: float, status: str, modified_by: str = "System") -> dict:
        result = self.model.insert_vehicle(v_id, plate, v_type, capacity, status)
        if result is True:
            self.logger.log_action("CREATE", "Vehicle", v_id, modified_by, f"Added new {v_type} | Plate: {plate} | Cap: {capacity}kg")
            return {"success": True, "message": f"Vehicle {v_id} added successfully!"}
        else:
            return {"success": False, "message": "Error: Vehicle ID might already exist."}

    def modify_vehicle(self, v_id: str, plate: str, v_type: str, capacity: float, status: str, modified_by: str = "System") -> dict:
        result = self.model.update_vehicle(v_id, plate, v_type, capacity, status, modified_by)
        if result is True:
            log_details = f"Plate: {plate} | Type: {v_type} | Cap: {capacity}kg | Status: {status}"
            self.logger.log_action("UPDATE", "Vehicle", v_id, modified_by, log_details)
            return {"success": True, "message": f"Vehicle {v_id} updated successfully!"}
        else:
            return {"success": False, "message": "Error updating vehicle."}

    def remove_vehicle(self, v_id: str, modified_by: str = "System") -> dict:
        result = self.model.delete_vehicle(v_id)
        if result is True:
            self.logger.log_action("DELETE", "Vehicle", v_id, modified_by, "Deleted vehicle from fleet database")
            return {"success": True, "message": "Vehicle deleted successfully!"}
        else:
            return {"success": False, "message": "Error deleting vehicle."}