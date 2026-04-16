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
                
                # 1. Numaram Cererile in asteptare
                try:
                    db_cursor.execute("SELECT COUNT(id) FROM transport_requests WHERE status = 'Pending'")
                    counts["pending_requests"] = db_cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    pass
                
                # 2. Numaram Masinile disponibile
                try:
                    db_cursor.execute("SELECT COUNT(id) FROM vehicles WHERE status = 'Available'")
                    counts["available_vehicles"] = db_cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    pass
                
                # 3. Numaram Soferii disponibili
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
                # Extragem doar cele 5 coloane necesare vizualizarii in Dashboard
                db_cursor.execute("SELECT id, client, pickup, delivery, status FROM transport_requests ORDER BY id DESC LIMIT 10")
                for row in db_cursor.fetchall():
                    requests.append(dict(row))
        except sqlite3.Error as e:
            logging.error(f"Dashboard Recent Requests Error: {e}")
            
        return requests