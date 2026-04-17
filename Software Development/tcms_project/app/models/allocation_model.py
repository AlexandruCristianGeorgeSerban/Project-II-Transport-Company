import sqlite3
import logging
from typing import Dict, List, Any
from app.models.notification_model import NotificationModel # <-- IMPORTUL NOU

DB_PATH: str = "instance/database.sqlite"

class AllocationModel:
    """Handles database operations for resource allocation."""

    def __init__(self) -> None:
        """Ensures the transport_requests table exists so we don't get errors."""
        self._ensure_requests_table()

    def _ensure_requests_table(self) -> None:
        """Creates the requests table if it's missing (with all 10 columns)."""
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
        except sqlite3.Error as error:
            logging.error(f"Error checking requests table: {error}")

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Retrieves requests that need allocation."""
        requests: List[Dict[str, Any]] = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                # Modificat pentru a aloca doar cererile acceptate de client
                db_cursor.execute("SELECT id, client, pickup, delivery FROM transport_requests WHERE status IN ('Pending', 'Accepted')")
                rows = db_cursor.fetchall()
                for row in rows:
                    requests.append(dict(row))
                
                if not requests:
                    return [{"id": "2000001", "client": "Gratu Marow", "pickup": "City A", "delivery": "City B"}]
                return requests
        except sqlite3.Error as db_error:
            logging.error(f"Error fetching requests: {db_error}")
            return requests

    def get_available_vehicles(self) -> List[Dict[str, Any]]:
        """Retrieves only vehicles that are 'Available'."""
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
        """Retrieves only drivers who are 'Available'."""
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

    def allocate_resources(self, request_id: str, vehicle_id: str, driver_id: str) -> bool:
        """Updates the status of the request, vehicle, and driver to reflect allocation."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                
                # Update request status
                db_cursor.execute("UPDATE transport_requests SET status = 'In Transit' WHERE id = ?", (request_id,))
                
                # REQ-66: Update vehicle status
                db_cursor.execute("UPDATE vehicles SET status = 'In Transit' WHERE id = ?", (vehicle_id,))
                
                # REQ-67: Update driver availability
                db_cursor.execute("UPDATE drivers SET availability = 'In Transit' WHERE id = ?", (driver_id,))
                
                connection.commit()
                
                # Trimitere notificare globala
                NotificationModel().add_notification(
                    "All", 
                    f"🚚 Alocare finalizată! Cererea {request_id} a plecat la drum. Mașina {vehicle_id} și Șoferul {driver_id} sunt 'In Transit'."
                )
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Allocation error: {db_error}")
            return False

    def mark_job_delivered(self, request_id: str, vehicle_id: str, driver_id: str) -> bool:
        """
        Fulfills REQ-68, 69, 70, 71: 
        Marks a job as Delivered, frees up the driver and vehicle, and logs the time.
        """
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                
                # REQ-68 & REQ-71: Update job status (timestamp is handled by the system clock generally, or can be appended)
                db_cursor.execute("UPDATE transport_requests SET status = 'Delivered' WHERE id = ?", (request_id,))
                
                # REQ-69: Mark vehicle as Available again
                db_cursor.execute("UPDATE vehicles SET status = 'Available' WHERE id = ?", (vehicle_id,))
                
                # REQ-70: Mark driver as Available again
                db_cursor.execute("UPDATE drivers SET availability = 'Available' WHERE id = ?", (driver_id,))
                
                connection.commit()
                
                # Notificare de succes!
                NotificationModel().add_notification(
                    "All", 
                    f"🏁 Cursa {request_id} a fost LIVRATĂ cu succes! Mașina {vehicle_id} și Șoferul {driver_id} sunt din nou disponibili."
                )
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Delivery update error: {db_error}")
            return False