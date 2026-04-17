import sqlite3
import logging
from typing import List, Dict, Any

DB_PATH: str = "instance/database.sqlite"

class SupportModel:
    def create_table(self) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                # Tabelul principal (Tichete)
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
                # Tabelul secundar (Conversatia)
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ticket_replies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticket_id INTEGER NOT NULL,
                        sender TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
                    ticket = dict(row)
                    # Aducem tot istoricul conversatiei pentru acest tichet
                    replies_cursor = connection.execute("SELECT * FROM ticket_replies WHERE ticket_id = ? ORDER BY timestamp ASC", (ticket['id'],))
                    ticket['replies'] = [dict(r) for r in replies_cursor.fetchall()]
                    tickets.append(ticket)
                return tickets
        except sqlite3.Error as e:
            logging.error(f"Fetch all error: {e}")
            return tickets

    def get_tickets_by_client(self, client_name: str) -> List[Dict[str, Any]]:
        tickets = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                cursor = connection.execute("SELECT * FROM support_tickets WHERE client = ? ORDER BY id DESC", (client_name,))
                for row in cursor.fetchall():
                    ticket = dict(row)
                    # Aducem tot istoricul si pentru client
                    replies_cursor = connection.execute("SELECT * FROM ticket_replies WHERE ticket_id = ? ORDER BY timestamp ASC", (ticket['id'],))
                    ticket['replies'] = [dict(r) for r in replies_cursor.fetchall()]
                    tickets.append(ticket)
                return tickets
        except sqlite3.Error as e:
            logging.error(f"Fetch client tickets error: {e}")
            return tickets

    def add_reply(self, ticket_id: int, sender: str, message: str) -> bool:
        """Adauga un mesaj nou in conversatie si schimba statusul tichetului."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                # 1. Adaugam mesajul
                connection.execute(
                    "INSERT INTO ticket_replies (ticket_id, sender, message) VALUES (?, ?, ?)",
                    (ticket_id, sender, message)
                )
                # 2. Modificam statusul ca sa stim a cui e "mingea"
                new_status = 'Answered' if sender in ['Staff', 'Administrator'] else 'Client Replied'
                connection.execute("UPDATE support_tickets SET status = ? WHERE id = ?", (new_status, ticket_id))
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Add reply error: {e}")
            return False

    def delete_ticket(self, ticket_id: int) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.execute("DELETE FROM support_tickets WHERE id = ?", (ticket_id,))
                connection.execute("DELETE FROM ticket_replies WHERE ticket_id = ?", (ticket_id,)) # Stergem si conversatia!
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Delete error: {e}")
            return False