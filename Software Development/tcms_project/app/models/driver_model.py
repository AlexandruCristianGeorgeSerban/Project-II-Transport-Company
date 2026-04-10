import sqlite3
import logging
from typing import Dict, List, Any

DB_PATH: str = "instance/database.sqlite"

class DriverModel:
    """Handles direct CRUD database operations for the company drivers."""

    def create_table(self) -> bool:
        """Creates the drivers table if it does not already exist."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS drivers (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        licenses TEXT NOT NULL,
                        experience TEXT NOT NULL,
                        dob TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        address TEXT NOT NULL,
                        availability TEXT NOT NULL
                    )
                """)
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Database error during drivers table creation: {error}")
            return False

    def insert_driver(self, d_id: str, name: str, status: str, licenses: str, exp: str, dob: str, doc_id: str, address: str, avail: str) -> bool:
        """Inserts a new driver record securely into the database."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute(
                    "INSERT INTO drivers (id, name, status, licenses, experience, dob, document_id, address, availability) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (d_id, name, status, licenses, exp, dob, doc_id, address, avail)
                )
                connection.commit()
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Insert error: {db_error}")
            return False

    def update_driver(self, d_id: str, name: str, status: str, licenses: str, exp: str, dob: str, doc_id: str, address: str, avail: str) -> bool:
        """Updates an existing driver's data securely."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute(
                    "UPDATE drivers SET name = ?, status = ?, licenses = ?, experience = ?, dob = ?, document_id = ?, address = ?, availability = ? WHERE id = ?",
                    (name, status, licenses, exp, dob, doc_id, address, avail, d_id)
                )
                connection.commit()
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Update error: {db_error}")
            return False

    def delete_driver(self, d_id: str) -> bool:
        """Deletes a driver record from the database."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("DELETE FROM drivers WHERE id = ?", (d_id,))
                connection.commit()
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Delete error: {db_error}")
            return False

    def get_all_drivers(self) -> List[Dict[str, Any]]:
        """Retrieves the list of all registered drivers."""
        drivers: List[Dict[str, Any]] = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT * FROM drivers ORDER BY name")
                rows = db_cursor.fetchall()
                for row in rows:
                    drivers.append(dict(row))
                return drivers
        except sqlite3.Error as db_error:
            logging.error(f"Error retrieving driver list: {db_error}")
            return drivers

    def get_driver_summary(self) -> Dict[str, int]:
        """Retrieves exact counts for total, active, and on-leave drivers."""
        summary: Dict[str, int] = {"total": 0, "active": 0, "on_leave": 0}
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                
                db_cursor.execute("SELECT COUNT(id) FROM drivers")
                summary["total"] = db_cursor.fetchone()[0]
                
                db_cursor.execute("SELECT COUNT(id) FROM drivers WHERE status = ?", ("Active",))
                summary["active"] = db_cursor.fetchone()[0]
                
                db_cursor.execute("SELECT COUNT(id) FROM drivers WHERE availability = ?", ("On Leave",))
                summary["on_leave"] = db_cursor.fetchone()[0]
                
                return summary
        except sqlite3.Error as database_error:
            logging.error(f"Error retrieving driver summary: {database_error}")
            return summary