from typing import Dict, Any
import logging
from app.models.dashboard_model import DashboardModel

class DashboardController:
    """Processes business logic for dashboard CRUD operations."""

    def __init__(self) -> None:
        """Initializes the dashboard model and ensures the DB table exists."""
        self.model = DashboardModel()
        self.model.create_table()

    def load_dashboard_data(self) -> Dict[str, Any]:
        """Loads and structures data for the UI."""
        dashboard_data: Dict[str, Any] = {}
        try:
            dashboard_data["counts"] = self.model.get_summary_counts()
            dashboard_data["recent_requests"] = self.model.get_recent_requests()
            return dashboard_data
        except Exception as logic_error:
            logging.error(f"Error processing dashboard data: {logic_error}")
            dashboard_data["counts"] = {"pending_requests": 0, "available_vehicles": 0, "available_drivers": 0}
            dashboard_data["recent_requests"] = []
            return dashboard_data

    def add_new_request(self, client: str, pickup: str, delivery: str, status: str) -> dict:
        """Handles the logic to create a new request."""
        if not client or not pickup or not delivery:
            return {"success": False, "message": "All fields are required."}
        else:
            result = self.model.insert_request(client, pickup, delivery, status)
            if result is True:
                return {"success": True, "message": "Request added successfully."}
            else:
                return {"success": False, "message": "Database error while adding request."}

    def remove_request(self, request_id: int) -> dict:
        """Handles the logic to delete a request."""
        result = self.model.delete_request(request_id)
        if result is True:
            return {"success": True, "message": "Request deleted successfully."}
        else:
            return {"success": False, "message": "Database error while deleting request."}
            
    def modify_request(self, request_id: int, client: str, pickup: str, delivery: str, status: str) -> dict:
        """Handles the logic to update an existing request."""
        if not client or not pickup or not delivery:
            return {"success": False, "message": "All fields are required for an update."}
        else:
            result = self.model.update_request(request_id, client, pickup, delivery, status)
            if result is True:
                return {"success": True, "message": "Request updated successfully."}
            else:
                return {"success": False, "message": "Database error while updating the request."}