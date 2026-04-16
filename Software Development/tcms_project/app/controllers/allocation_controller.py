import logging
from typing import Dict, Any
from app.models.allocation_model import AllocationModel

class AllocationController:
    """Processes business logic for resource allocation."""

    def __init__(self) -> None:
        """Initializes the allocation model."""
        self.model = AllocationModel()

    def load_allocation_data(self) -> Dict[str, Any]:
        """Loads all available resources and pending requests."""
        data: Dict[str, Any] = {}
        try:
            data["requests"] = self.model.get_pending_requests()
            data["vehicles"] = self.model.get_available_vehicles()
            data["drivers"] = self.model.get_available_drivers()
            return data
        except Exception as error:
            logging.error(f"Logic error loading allocation data: {error}")
            return {"requests": [], "vehicles": [], "drivers": []}

    def process_allocation(self, req_id: str, veh_id: str, drv_id: str) -> dict:
        """Handles the allocation confirmation."""
        if not req_id or not veh_id or not drv_id:
            return {"success": False, "message": "Please select a Request, a Vehicle, and a Driver!"}
            
        result = self.model.allocate_resources(req_id, veh_id, drv_id)
        
        if result is True:
            return {"success": True, "message": f"Successfully allocated Vehicle {veh_id} and Driver {drv_id} to Request {req_id}!"}
        else:
            return {"success": False, "message": "An error occurred during allocation."}