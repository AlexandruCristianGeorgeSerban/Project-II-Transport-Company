import sqlite3
import logging
from typing import Dict, List, Any

DB_PATH: str = "instance/database.sqlite"

class RequestModel:
    """Handles direct CRUD database operations for transport requests."""

    def create_table(self) -> bool:
        """Creates the transport_requests and negotiation_chat tables."""
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
                        vehicle_type TEXT, 
                        estimated_price REAL,
                        price_offer REAL, 
                        current_lat REAL, 
                        current_lng REAL, 
                        assigned_driver TEXT DEFAULT NULL, 
                        assigned_vehicle TEXT DEFAULT NULL
                    )
                """)
                
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS negotiation_chat (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        request_id TEXT NOT NULL,
                        sender TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
                    )
                """)

                # Adaugam noile coloane de securitate & amprenta
                columns_to_add = [
                    ("transport_requests", "last_modified_by", "TEXT DEFAULT 'System'"),
                    ("transport_requests", "last_modified_at", "DATETIME DEFAULT (datetime('now', 'localtime'))"),
                    ("transport_requests", "offer_expires_at", "DATETIME DEFAULT NULL")
                ]
                for table, col, definition in columns_to_add:
                    try:
                        db_cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
                    except sqlite3.OperationalError:
                        pass
                        
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Database error during requests table creation: {error}")
            return False

    def insert_request(self, r_id: str, client: str, c_type: str, desc: str, weight: float, volume: float, pickup: str, delivery: str, date: str, status: str) -> bool:
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

    def update_request(self, r_id: str, client: str, c_type: str, desc: str, weight: float, volume: float, pickup: str, delivery: str, date: str, status: str, staff_username: str = 'Unknown') -> bool:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("""
                    UPDATE transport_requests 
                    SET client = ?, cargo_type = ?, description = ?, weight = ?, volume = ?, pickup = ?, delivery = ?, preferred_date = ?, status = ?,
                        last_modified_by = ?, last_modified_at = datetime('now', 'localtime')
                    WHERE id = ?
                """, (client, c_type, desc, weight, volume, pickup, delivery, date, status, staff_username, r_id))
                connection.commit()
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Update error: {db_error}")
            return False

    def delete_request(self, r_id: str) -> bool:
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

    def update_request_status_and_price(self, req_id: str, new_status: str, price: float) -> dict:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("""
                    UPDATE transport_requests 
                    SET status = ?, price_offer = ?, offer_expires_at = datetime('now', 'localtime', '+24 hours')
                    WHERE id = ?
                """, (new_status, price, req_id))
                connection.commit()
                return {"success": True, "message": f"Oferta de ${price} a fost trimisă. Expiră în 24 de ore!"}
        except sqlite3.Error as db_error:
            return {"success": False, "message": "A apărut o eroare la salvarea ofertei."}
            
    def update_request_status(self, req_id: str, new_status: str) -> dict:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("UPDATE transport_requests SET status = ? WHERE id = ?", (new_status, req_id))
                connection.commit()
                return {"success": True, "message": f"Cererea #{req_id} a fost marcată ca {new_status}."}
        except sqlite3.Error as db_error:
            return {"success": False, "message": "Eroare la salvarea în baza de date."}

    def get_request_by_id(self, r_id: str) -> Dict[str, Any]:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                row = connection.execute("SELECT * FROM transport_requests WHERE id = ?", (r_id,)).fetchone()
                return dict(row) if row else {}
        except sqlite3.Error:
            return {}

    def add_negotiation_message(self, r_id: str, sender: str, message: str) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.execute("INSERT INTO negotiation_chat (request_id, sender, message) VALUES (?, ?, ?)", (r_id, sender, message))
                connection.commit()
                return True
        except sqlite3.Error:
            return False

    def get_negotiation_messages(self, r_id: str) -> List[Dict[str, Any]]:
        messages = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                rows = connection.execute("SELECT * FROM negotiation_chat WHERE request_id = ? ORDER BY timestamp ASC", (r_id,)).fetchall()
                for row in rows:
                    messages.append(dict(row))
                return messages
        except sqlite3.Error:
            return messages