import logging
import sqlite3
from typing import Dict, Any
from app.models.dashboard_model import DashboardModel

DB_PATH = "instance/database.sqlite"

class DashboardController:
    """Processes business logic for dashboard views (Read-Only)."""

    def __init__(self) -> None:
        """Initializes the dashboard model."""
        self.model = DashboardModel()

    def _attach_negotiation_messages(self, requests_list: list) -> list:
        """Helper method care extrage istoricul de chat pentru cererile in negociere."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='negotiation_chat'")
                table_row = cursor.fetchone()
                
                if table_row:
                    for req in requests_list:
                        if req.get('status') == 'Negotiation':
                            cursor.execute("SELECT * FROM negotiation_chat WHERE request_id = ? ORDER BY timestamp ASC", (req['id'],))
                            
                            messages = []
                            for row in cursor.fetchall():
                                msg_dict = dict(row)
                                if str(msg_dict['sender']).startswith('Staff'):
                                    msg_dict['sender_role'] = 'Staff'
                                else:
                                    msg_dict['sender_role'] = 'Customer'
                                messages.append(msg_dict)
                                
                            req['messages'] = messages
                        else:
                            req['messages'] = []
                else:
                    for req in requests_list:
                        req['messages'] = []
                        
        except Exception as e:
            logging.error(f"Error fetching negotiation messages: {e}")
            for req in requests_list:
                if 'messages' not in req:
                    req['messages'] = []
                    
        return requests_list

    def load_dashboard_data(self) -> Dict[str, Any]:
        """Loads and structures data for the UI."""
        dashboard_data: Dict[str, Any] = {}
        try:
            dashboard_data["counts"] = self.model.get_summary_counts()
            
            recent_reqs = self.model.get_recent_requests()
            dashboard_data["recent_requests"] = self._attach_negotiation_messages(recent_reqs)
            
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
            
            recent_reqs = self.model.get_recent_requests()
            staff_data["requests"] = self._attach_negotiation_messages(recent_reqs)
            
            staff_data["schedule"] = self.model.get_todays_schedule()
            return staff_data
        except Exception as logic_error:
            logging.error(f"Error processing staff dashboard data: {logic_error}")
            staff_data["counts"] = {"pending_allocations": 0, "unread_tickets": 0, "pending_invoices": 0}
            staff_data["requests"] = [] 
            staff_data["schedule"] = []
            return staff_data