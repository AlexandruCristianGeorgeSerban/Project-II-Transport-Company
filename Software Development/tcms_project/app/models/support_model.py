import sqlite3
import logging
from typing import List, Dict, Any

DB_PATH: str = "instance/database.sqlite"

class SupportModel:
    def create_table(self) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS support_tickets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client TEXT NOT NULL,
                        message TEXT NOT NULL,
                        admin_response TEXT DEFAULT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'New'
                    )
                """)
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Error: {error}")
            return False

    def insert_ticket(self, client: str, message: str) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.execute("INSERT INTO support_tickets (client, message) VALUES (?, ?)", (client, message))
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Insert error: {e}")
            return False

    def get_all_tickets(self) -> List[Dict[str, Any]]:
        tickets = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                cursor = connection.execute("SELECT * FROM support_tickets ORDER BY id DESC")
                for row in cursor.fetchall():
                    tickets.append(dict(row))
                return tickets
        except sqlite3.Error as e:
            logging.error(f"Fetch all error: {e}")
            return tickets

    def get_tickets_by_client(self, client_name: str) -> List[Dict[str, Any]]:
        """Aduce tichetele doar pentru un anumit client."""
        tickets = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                cursor = connection.execute("SELECT * FROM support_tickets WHERE client = ? ORDER BY id DESC", (client_name,))
                for row in cursor.fetchall():
                    tickets.append(dict(row))
                return tickets
        except sqlite3.Error as e:
            logging.error(f"Fetch client tickets error: {e}")
            return tickets

    def update_response(self, ticket_id: int, response_text: str) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.execute(
                    "UPDATE support_tickets SET admin_response = ?, status = 'Answered' WHERE id = ?",
                    (response_text, ticket_id)
                )
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Update response error: {e}")
            return False

    def delete_ticket(self, ticket_id: int) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.execute("DELETE FROM support_tickets WHERE id = ?", (ticket_id,))
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Delete error: {e}")
            return False