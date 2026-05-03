import sqlite3
import logging
from typing import Dict, List, Any, Optional

DB_PATH: str = "instance/database.sqlite"

class FleetModel:
    """Handles direct CRUD operations for the company fleet."""

    def create_table(self) -> bool:
        """Creates the vehicles table if it does not already exist."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vehicles (
                        id TEXT PRIMARY KEY,
                        plate_number TEXT NOT NULL,
                        type TEXT NOT NULL,
                        capacity INTEGER NOT NULL,
                        status TEXT NOT NULL
                    )
                """)
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Database error during vehicles table creation: {error}")
            return False

    def insert_vehicle(self, vehicle_id: str, plate: str, v_type: str, capacity: int, status: str) -> bool:
        """Inserts a new vehicle record securely into the database."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute(
                    "INSERT INTO vehicles (id, plate_number, type, capacity, status) VALUES (?, ?, ?, ?, ?)",
                    (vehicle_id, plate, v_type, capacity, status)
                )
                connection.commit()
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Insert error: {db_error}")
            return False

    def delete_vehicle(self, vehicle_id: str) -> bool:
        """Deletes a vehicle record from the database based on ID."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
                connection.commit()
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Delete error: {db_error}")
            return False

    def get_fleet_summary(self) -> Dict[str, int]:
        """Retrieves exact counts for total, active, and maintenance vehicles directly from DB."""
        summary: Dict[str, int] = {"total": 0, "active": 0, "maintenance": 0}
        
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                
                db_cursor.execute("SELECT COUNT(id) FROM vehicles")
                summary["total"] = db_cursor.fetchone()[0]
                
                db_cursor.execute("SELECT COUNT(id) FROM vehicles WHERE status != ?", ("Maintenance",))
                summary["active"] = db_cursor.fetchone()[0]
                
                db_cursor.execute("SELECT COUNT(id) FROM vehicles WHERE status = ?", ("Maintenance",))
                summary["maintenance"] = db_cursor.fetchone()[0]
                
                return summary
        except sqlite3.Error as database_error:
            logging.error(f"Error retrieving fleet summary counts: {database_error}")
            return summary

    def get_all_vehicles(self) -> List[Dict[str, Any]]:
        """Retrieves the list of all registered vehicles."""
        vehicles: List[Dict[str, Any]] = []
        
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT id, plate_number, type, capacity, status FROM vehicles ORDER BY id")
                rows = db_cursor.fetchall()
                
                for row in rows:
                    vehicles.append(dict(row))
                
                return vehicles
        except sqlite3.Error as db_error:
            logging.error(f"Error retrieving vehicle list: {db_error}")
            return vehicles
    
    def update_vehicle(self, v_id: str, plate: str, v_type: str, capacity: int, status: str) -> bool:
        """Updates an existing vehicle's data securely."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute(
                    "UPDATE vehicles SET plate_number = ?, type = ?, capacity = ?, status = ? WHERE id = ?",
                    (plate, v_type, capacity, status, v_id)
                )
                connection.commit()
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Update error: {db_error}")
            return False

    def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific vehicle's details based on its ID."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
                row = db_cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except sqlite3.Error as db_error:
            logging.error(f"Error retrieving vehicle by ID {vehicle_id}: {db_error}")
            return None