import logging
from typing import Dict, Any
from app.models.dashboard_model import DashboardModel

class DashboardController:
    """Processes business logic for dashboard views (Read-Only)."""

    def __init__(self) -> None:
        """Initializes the dashboard model."""
        self.model = DashboardModel()

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
        
    def load_staff_dashboard_data(self) -> Dict[str, Any]:
        """Loads and structures data specifically for the Staff UI."""
        staff_data: Dict[str, Any] = {}
        try:
            
            staff_data["counts"] = self.model.get_staff_summary_counts()
            
            
            staff_data["requests"] = self.model.get_recent_requests()
            
            staff_data["schedule"] = self.model.get_todays_schedule()
            return staff_data
        except Exception as logic_error:
            logging.error(f"Error processing staff dashboard data: {logic_error}")
            staff_data["counts"] = {"pending_allocations": 0, "unread_tickets": 0, "pending_invoices": 0}
            
           
            staff_data["requests"] = [] 
            
            staff_data["schedule"] = []
            return staff_data