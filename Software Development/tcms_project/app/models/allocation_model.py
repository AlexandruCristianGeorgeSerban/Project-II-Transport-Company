import sqlite3
import logging
from typing import Dict, List, Any

DB_PATH: str = "instance/database.sqlite"

class AllocationModel:
    """Handles database operations for resource allocation."""

    def __init__(self) -> None:
        self._ensure_requests_table()

    def _ensure_requests_table(self) -> None:
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
                for row in db_cursor.fetchall():
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
                for row in db_cursor.fetchall():
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
                for row in db_cursor.fetchall():
                    drivers.append(dict(row))
                return drivers
        except sqlite3.Error as db_error:
            logging.error(f"Error fetching available drivers: {db_error}")
            return drivers

    def get_allocation_constraints(self, req_id: str, veh_id: str, drv_id: str) -> dict:
        data = {"weight": 0.0, "capacity": 0.0, "vehicle_type": "", "driver_licenses": ""}
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT weight FROM transport_requests WHERE id = ?", (req_id,))
                req = cursor.fetchone()
                if req: data["weight"] = float(req["weight"])
                
                cursor.execute("SELECT capacity, type FROM vehicles WHERE id = ?", (veh_id,))
                veh = cursor.fetchone()
                if veh: 
                    data["capacity"] = float(veh["capacity"])
                    data["vehicle_type"] = veh["type"]
                    
                cursor.execute("SELECT licenses FROM drivers WHERE id = ?", (drv_id,))
                drv = cursor.fetchone()
                if drv: data["driver_licenses"] = drv["licenses"]
                
        except (sqlite3.Error, ValueError) as e:
            logging.error(f"Constraint fetch error: {e}")
        return data

    def allocate_resources(self, request_id: str, vehicle_id: str, driver_id: str, staff_username: str = "Unknown") -> bool:
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
                    SELECT tr.id, tr.client, tr.cargo_type, tr.pickup, tr.delivery, 
                           tr.estimated_price, tr.price_offer, tr.status, 
                           tr.vehicle_id, v.plate_number, 
                           tr.driver_id, d.name AS driver_name
                    FROM transport_requests tr
                    LEFT JOIN vehicles v ON CAST(tr.vehicle_id AS TEXT) = CAST(v.id AS TEXT)
                    LEFT JOIN drivers d ON CAST(tr.driver_id AS TEXT) = CAST(d.id AS TEXT)
                    WHERE tr.status = 'In Transit'
                """)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Error fetching active jobs: {e}")
            return []

    def cancel_job(self, req_id: str) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT vehicle_id, driver_id FROM transport_requests WHERE id = ?", (req_id,))
                row = cursor.fetchone()
                
                if row:
                    veh_id, drv_id = row
                    cursor.execute("UPDATE transport_requests SET status = 'Cancelled' WHERE id = ?", (req_id,))
                    if veh_id:
                        cursor.execute("UPDATE vehicles SET status = 'Available' WHERE id = ?", (veh_id,))
                    if drv_id:
                        cursor.execute("UPDATE drivers SET availability = 'Available' WHERE id = ?", (drv_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Error cancelling job: {e}")
            return False