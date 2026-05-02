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
                        user_id INTEGER, 
                        client TEXT NOT NULL,
                        subject TEXT, 
                        message TEXT NOT NULL,
                        admin_response TEXT DEFAULT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'Pending'
                    )
                """)
                # Tabelul secundar (Conversatia Helpdesk)
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ticket_replies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticket_id INTEGER NOT NULL,
                        sender TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # NOU: Tabelul pentru Chat Privat (Driver <-> Customer)
                # Am pus job_id ca TEXT pentru ca ai ID-uri de tipul REQ-123456
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS job_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id TEXT NOT NULL,
                        sender_id INTEGER NOT NULL,
                        sender_role TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Error: {error}")
            return False

    # --- FUNCTII PENTRU CHAT PRIVAT (JOB MESSAGES) ---

    def add_job_message(self, job_id: str, sender_id: int, role: str, message: str) -> bool:
        """Adauga un mesaj in chatul specific unui transport."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.execute(
                    "INSERT INTO job_messages (job_id, sender_id, sender_role, message) VALUES (?, ?, ?, ?)",
                    (str(job_id), sender_id, role, message)
                )
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Error adding job message: {e}")
            return False

    def get_job_messages(self, job_id: str) -> List[Dict[str, Any]]:
        """Aduce istoricul mesajelor pentru un transport specific."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                cursor = connection.execute("SELECT * FROM job_messages WHERE job_id = ? ORDER BY timestamp ASC", (str(job_id),))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Error fetching job messages: {e}")
            return []

    # --- FUNCTII PENTRU HELPDESK TICKET SYSTEM ---

    def insert_ticket(self, client: str, message: str) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.execute("INSERT INTO support_tickets (client, message) VALUES (?, ?)", (client, message))
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Insert error: {e}")
            return False

    def create_ticket(self, user_id: int, client: str, subject: str, message: str) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                cursor = connection.cursor()
                cursor.execute("PRAGMA table_info(support_tickets)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'user_id' not in columns or 'subject' not in columns:
                   connection.execute("INSERT INTO support_tickets (client, message) VALUES (?, ?)", (client, f"[{subject}] {message}"))
                else:
                    connection.execute("INSERT INTO support_tickets (user_id, client, subject, message) VALUES (?, ?, ?, ?)", (user_id, client, subject, message))
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Create ticket error: {e}")
            return False

    def get_user_tickets(self, user_id: int) -> List[Dict[str, Any]]:
        tickets = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                cursor = connection.cursor()
                cursor.execute("PRAGMA table_info(support_tickets)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'user_id' in columns:
                    cursor = connection.execute("SELECT * FROM support_tickets WHERE user_id = ? ORDER BY id DESC", (user_id,))
                else:
                    return tickets 
                    
                for row in cursor.fetchall():
                    ticket = dict(row)
                    replies_cursor = connection.execute("SELECT * FROM ticket_replies WHERE ticket_id = ? ORDER BY timestamp ASC", (ticket['id'],))
                    
                    replies = [dict(r) for r in replies_cursor.fetchall()]
                    reply_text = ""
                    for rep in replies:
                         reply_text += f"[{rep['timestamp']}] {rep['sender']}: {rep['message']}\n"
                         
                    ticket['replies'] = reply_text
                    
                    if 'subject' not in ticket:
                        ticket['subject'] = "Support Request"
                        
                    tickets.append(ticket)
                return tickets
        except sqlite3.Error as e:
            logging.error(f"Fetch user tickets error: {e}")
            return tickets

    def get_all_tickets(self) -> List[Dict[str, Any]]:
        tickets = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                cursor = connection.execute("SELECT * FROM support_tickets ORDER BY id DESC")
                for row in cursor.fetchall():
                    ticket = dict(row)
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
                    replies_cursor = connection.execute("SELECT * FROM ticket_replies WHERE ticket_id = ? ORDER BY timestamp ASC", (ticket['id'],))
                    ticket['replies'] = [dict(r) for r in replies_cursor.fetchall()]
                    tickets.append(ticket)
                return tickets
        except sqlite3.Error as e:
            logging.error(f"Fetch client tickets error: {e}")
            return tickets

    def add_reply(self, ticket_id: int, sender: str, message: str) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.execute(
                    "INSERT INTO ticket_replies (ticket_id, sender, message) VALUES (?, ?, ?)",
                    (ticket_id, sender, message)
                )
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
                connection.execute("DELETE FROM ticket_replies WHERE ticket_id = ?", (ticket_id,))
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Delete error: {e}")
            return False