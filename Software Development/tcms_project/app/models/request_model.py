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
                # Tabela se bazează acum pe migrarea din update_db
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

    def update_request_status_and_price(self, req_id: str, new_status: str, price: float) -> dict:
        """Actualizează statusul și prețul ferm (price_offer) al unei cereri."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                
                # Salvăm în price_offer, care este valoarea ce va fi folosită la factură/rapoarte
                db_cursor.execute("""
                    UPDATE transport_requests 
                    SET status = ?, price_offer = ? 
                    WHERE id = ?
                """, (new_status, price, req_id))
                
                connection.commit()
                return {"success": True, "message": f"Oferta de {price} a fost trimisă cu succes pentru cererea #{req_id}!"}
        except sqlite3.Error as db_error:
            logging.error(f"Eroare la actualizarea ofertei de preț: {db_error}")
            return {"success": False, "message": "A apărut o eroare la salvarea în baza de date."}
            
    def update_request_status(self, req_id: str, new_status: str) -> dict:
        """Actualizează doar statusul unei cereri."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("UPDATE transport_requests SET status = ? WHERE id = ?", (new_status, req_id))
                connection.commit()
                return {"success": True, "message": f"Cererea #{req_id} a fost marcată ca {new_status}."}
        except sqlite3.Error as db_error:
            logging.error(f"Eroare la actualizarea statusului: {db_error}")
            return {"success": False, "message": "Eroare la salvarea în baza de date."}