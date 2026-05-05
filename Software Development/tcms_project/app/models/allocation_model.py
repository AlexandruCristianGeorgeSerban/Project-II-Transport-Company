import sqlite3
import logging
from typing import Dict, List, Any
from app.models.notification_model import NotificationModel

DB_PATH: str = "instance/database.sqlite"

class AllocationModel:
    """Handles database operations for resource allocation."""

    def __init__(self) -> None:
        """Ensures the transport_requests table exists so we don't get errors."""
        self._ensure_requests_table()

    def _ensure_requests_table(self) -> None:
        """Creates the requests table if it's missing (with all required columns)."""
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
                        status TEXT NOT NULL,
                        vehicle_id TEXT,
                        driver_id TEXT,
                        estimated_price REAL
                    )
                """)
                
                try:
                    db_cursor.execute("ALTER TABLE transport_requests ADD COLUMN allocated_by TEXT DEFAULT 'System'")
                except sqlite3.OperationalError:
                    pass
                connection.commit()
        except sqlite3.Error as error:
            logging.error(f"Error checking requests table: {error}")

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        requests: List[Dict[str, Any]] = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT id, client, pickup, delivery FROM transport_requests WHERE status IN ('Pending', 'Accepted')")
                rows = db_cursor.fetchall()
                for row in rows:
                    requests.append(dict(row))
                return requests
        except sqlite3.Error as db_error:
            logging.error(f"Error fetching requests: {db_error}")
            return requests

    def get_available_vehicles(self) -> List[Dict[str, Any]]:
        vehicles: List[Dict[str, Any]] = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT id, plate_number, type, capacity FROM vehicles WHERE status = 'Available'")
                rows = db_cursor.fetchall()
                for row in rows:
                    vehicles.append(dict(row))
                return vehicles
        except sqlite3.Error as db_error:
            logging.error(f"Error fetching available vehicles: {db_error}")
            return vehicles

    def get_available_drivers(self) -> List[Dict[str, Any]]:
        drivers: List[Dict[str, Any]] = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT id, name, licenses FROM drivers WHERE availability = 'Available'")
                rows = db_cursor.fetchall()
                for row in rows:
                    drivers.append(dict(row))
                return drivers
        except sqlite3.Error as db_error:
            logging.error(f"Error fetching available drivers: {db_error}")
            return drivers

    def allocate_resources(self, request_id: str, vehicle_id: str, driver_id: str, staff_username: str = "Unknown") -> bool:
        """Updates the status of the request, vehicle, and driver to reflect allocation."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                
                
                db_cursor.execute("""
                    UPDATE transport_requests 
                    SET status = 'In Transit', vehicle_id = ?, driver_id = ?, allocated_by = ? 
                    WHERE id = ?
                """, (vehicle_id, driver_id, staff_username, request_id))
                
                db_cursor.execute("UPDATE vehicles SET status = 'In Transit' WHERE id = ?", (vehicle_id,))
                db_cursor.execute("UPDATE drivers SET availability = 'In Transit' WHERE id = ?", (driver_id,))
                
                connection.commit()
                
                NotificationModel().add_notification(
                    "All", 
                    f"🚚 Alocare finalizată! Cererea {request_id} a plecat la drum. Mașina {vehicle_id} și Șoferul {driver_id} sunt 'In Transit'."
                )
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Allocation error: {db_error}")
            return False

    def get_active_jobs(self) -> list:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, client, cargo_type, pickup, delivery, estimated_price, vehicle_id, driver_id, status
                    FROM transport_requests
                    WHERE status = 'In Transit'
                """)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Error fetching active jobs: {e}")
            return []

    def mark_job_delivered(self, req_id: str) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT vehicle_id, driver_id FROM transport_requests WHERE id = ?", (req_id,))
                row = cursor.fetchone()
                
                if row:
                    veh_id, drv_id = row
                    cursor.execute("UPDATE transport_requests SET status = 'Delivered' WHERE id = ?", (req_id,))
                    if veh_id:
                        cursor.execute("UPDATE vehicles SET status = 'Available' WHERE id = ?", (veh_id,))
                    if drv_id:
                        cursor.execute("UPDATE drivers SET availability = 'Available' WHERE id = ?", (drv_id,))
                        
                conn.commit()
                NotificationModel().add_notification(
                    "All", 
                    f"🏁 Cursa {req_id} a fost LIVRATĂ cu succes! Mașina și Șoferul sunt din nou disponibili."
                )
                return True
        except sqlite3.Error as e:
            logging.error(f"Error marking job delivered: {e}")
            return False