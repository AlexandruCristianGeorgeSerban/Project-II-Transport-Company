import sqlite3
import logging
from typing import Dict, List, Any

DB_PATH: str = "instance/database.sqlite"

class RequestModel:
    """Handles direct CRUD database operations for transport requests."""

    def create_table(self) -> bool:
        """Creates the transport_requests table if it does not already exist."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transport_requests (
                        id TEXT PRIMARY KEY,
                        client TEXT NOT NULL,
                        cargo_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        weight REAL NOT NULL,
                        volume REAL NOT NULL,
                        pickup TEXT NOT NULL,
                        delivery TEXT NOT NULL,
                        preferred_date TEXT NOT NULL,
                        status TEXT NOT NULL
                    )
                """)
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Database error during requests table creation: {error}")
            return False

    def insert_request(self, r_id: str, client: str, c_type: str, desc: str, weight: float, volume: float, pickup: str, delivery: str, date: str, status: str) -> bool:
        """Inserts a new transport request securely into the database."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute(
                    "INSERT INTO transport_requests (id, client, cargo_type, description, weight, volume, pickup, delivery, preferred_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (r_id, client, c_type, desc, weight, volume, pickup, delivery, date, status)
                )
                connection.commit()
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Insert error: {db_error}")
            return False

    def update_request(self, r_id: str, client: str, c_type: str, desc: str, weight: float, volume: float, pickup: str, delivery: str, date: str, status: str) -> bool:
        """Updates an existing transport request securely."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute(
                    "UPDATE transport_requests SET client = ?, cargo_type = ?, description = ?, weight = ?, volume = ?, pickup = ?, delivery = ?, preferred_date = ?, status = ? WHERE id = ?",
                    (client, c_type, desc, weight, volume, pickup, delivery, date, status, r_id)
                )
                connection.commit()
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Update error: {db_error}")
            return False

    def delete_request(self, r_id: str) -> bool:
        """Deletes a transport request record from the database."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("DELETE FROM transport_requests WHERE id = ?", (r_id,))
                connection.commit()
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Delete error: {db_error}")
            return False

    def get_all_requests(self) -> List[Dict[str, Any]]:
        """Retrieves the list of all submitted transport requests."""
        requests_list: List[Dict[str, Any]] = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT * FROM transport_requests ORDER BY id DESC")
                rows = db_cursor.fetchall()
                for row in rows:
                    requests_list.append(dict(row))
                return requests_list
        except sqlite3.Error as db_error:
            logging.error(f"Error retrieving request list: {db_error}")
            return requests_list

    def get_request_summary(self) -> Dict[str, int]:
        """Retrieves exact counts for total, pending, and approved requests."""
        summary: Dict[str, int] = {"total": 0, "pending": 0, "approved": 0}
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                
                db_cursor.execute("SELECT COUNT(id) FROM transport_requests")
                summary["total"] = db_cursor.fetchone()[0]
                
                db_cursor.execute("SELECT COUNT(id) FROM transport_requests WHERE status = ?", ("Pending",))
                summary["pending"] = db_cursor.fetchone()[0]
                
                db_cursor.execute("SELECT COUNT(id) FROM transport_requests WHERE status = ?", ("Approved",))
                summary["approved"] = db_cursor.fetchone()[0]
                
                return summary
        except sqlite3.Error as database_error:
            logging.error(f"Error retrieving request summary: {database_error}")
            return summary