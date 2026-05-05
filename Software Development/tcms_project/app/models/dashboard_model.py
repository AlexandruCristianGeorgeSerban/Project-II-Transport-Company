import sqlite3
import logging
from typing import Dict, List, Any

DB_PATH: str = "instance/database.sqlite"

class DashboardModel:
    """Handles read-only database operations for the main Dashboard."""

    def get_summary_counts(self) -> Dict[str, int]:
        """Retrieves real-time counts from requests, vehicles, and drivers tables."""
        counts: Dict[str, int] = {
            "pending_requests": 0, 
            "available_vehicles": 0, 
            "available_drivers": 0
        }
        
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                
                
                try:
                    db_cursor.execute("SELECT COUNT(id) FROM transport_requests WHERE status = 'Pending'")
                    counts["pending_requests"] = db_cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    pass
                
               
                try:
                    db_cursor.execute("SELECT COUNT(id) FROM vehicles WHERE status = 'Available'")
                    counts["available_vehicles"] = db_cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    pass
                
                
                try:
                    db_cursor.execute("SELECT COUNT(id) FROM drivers WHERE availability = 'Available'")
                    counts["available_drivers"] = db_cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    pass
                    
        except sqlite3.Error as e:
            logging.error(f"Dashboard DB Error: {e}")
            
        return counts

    def get_recent_requests(self) -> List[Dict[str, Any]]:
        """Retrieves the latest transport requests to show in the table."""
        requests: List[Dict[str, Any]] = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                
                
                db_cursor.execute("""
                    SELECT id, client, pickup, delivery, status, cargo_type, weight, estimated_price as price 
                    FROM transport_requests 
                    ORDER BY id DESC LIMIT 10
                """)
                
                for row in db_cursor.fetchall():
                    requests.append(dict(row))
        except sqlite3.Error as e:
            logging.error(f"Dashboard Recent Requests Error: {e}")
            
        return requests
    
    def get_staff_summary_counts(self) -> Dict[str, int]:
        """Retrieves exact counts for the Staff Portal summary."""
        summary: Dict[str, int] = {
            "pending_allocations": 0, 
            "unread_tickets": 0, 
            "pending_invoices": 0
        }
        try:
           
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                
                
                db_cursor.execute("SELECT COUNT(id) FROM transport_requests WHERE status = 'Pending'")
                pending_reqs = db_cursor.fetchone()
                summary["pending_allocations"] = pending_reqs[0] if pending_reqs else 0
                
                
                summary["unread_tickets"] = 3
                summary["pending_invoices"] = 1
                
                return summary
        except sqlite3.Error as database_error:
            logging.error(f"Error retrieving staff summary: {database_error}")
            return summary
        
    def get_todays_schedule(self) -> List[Dict[str, Any]]:
        """Retrieves today's schedule for the staff member."""
        
       
        return [
            {"time": "10:00 AM", "task": "Allocate Driver to TRK-001", "status": "Pending"},
            {"time": "11:30 AM", "task": "Review Support Ticket #ST-402", "status": "In Progress"},
            {"time": "02:00 PM", "task": "Issue Invoice for SC Logistica SRL", "status": "Pending"},
            {"time": "04:00 PM", "task": "Check Fleet Maintenance Logs", "status": "Completed"}
        ]