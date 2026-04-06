import sqlite3
import logging
from typing import Dict, List, Any

DB_PATH: str = "instance/database.sqlite"

class DashboardModel:
    """Handles CRUD database operations for the dashboard transport requests."""

    def create_table(self) -> bool:
        """Creates the transport_requests table if it does not exist."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transport_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client TEXT NOT NULL,
                        pickup TEXT NOT NULL,
                        delivery TEXT NOT NULL,
                        status TEXT NOT NULL
                    )
                """)
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Database error during transport_requests table creation: {error}")
            return False

    def insert_request(self, client: str, pickup: str, delivery: str, status: str) -> bool:
        """Creates a new transport request in the database (CREATE)."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute(
                    "INSERT INTO transport_requests (client, pickup, delivery, status) VALUES (?, ?, ?, ?)",
                    (client, pickup, delivery, status)
                )
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Error inserting request: {error}")
            return False

    def delete_request(self, request_id: int) -> bool:
        """Removes a transport request from the database by ID (DELETE)."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("DELETE FROM transport_requests WHERE id = ?", (request_id,))
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Error deleting request: {error}")
            return False

    def get_summary_counts(self) -> Dict[str, int]:
        """Retrieves statistics for the dashboard cards (READ)."""
        summary_data: Dict[str, int] = {"pending_requests": 0, "available_vehicles": 8, "available_drivers": 6}
        
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT COUNT(id) FROM transport_requests WHERE status = ?", ("Pending",))
                summary_data["pending_requests"] = db_cursor.fetchone()[0]
                return summary_data
        except sqlite3.Error as database_error:
            logging.error(f"Error retrieving summary counts: {database_error}")
            return summary_data

    def get_recent_requests(self) -> List[Dict[str, Any]]:
        """Retrieves all transport requests for the table (READ)."""
        recent_requests: List[Dict[str, Any]] = []
        
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT id, client, pickup, delivery, status FROM transport_requests ORDER BY id DESC")
                rows = db_cursor.fetchall()
                
                for row in rows:
                    recent_requests.append(dict(row))
                    
                return recent_requests
        except sqlite3.Error as db_error:
            logging.error(f"Error retrieving recent requests: {db_error}")
            return recent_requests

    def update_request(self, request_id: int, client: str, pickup: str, delivery: str, status: str) -> bool:
        """Updates an existing transport request in the database (UPDATE)."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute(
                    "UPDATE transport_requests SET client = ?, pickup = ?, delivery = ?, status = ? WHERE id = ?",
                    (client, pickup, delivery, status, request_id)
                )
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Error updating request: {error}")
            return False