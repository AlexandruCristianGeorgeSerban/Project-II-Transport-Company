import sqlite3
import logging
from typing import List, Dict, Any

DB_PATH: str = "instance/database.sqlite"

class SupportModel:
    def __init__(self):
        """Inițializează modelul și se asigură că tabelele și coloanele necesare există."""
        self.db_path = DB_PATH
        self.create_table()

    def create_table(self) -> bool:
        """Creează tabelele și adaugă coloanele noi prin ALTER TABLE dacă este necesar."""
        try:
            with sqlite3.connect(self.db_path) as connection:
                db_cursor = connection.cursor()
                
                
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS support_tickets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER, 
                        client TEXT NOT NULL,
                        client_role TEXT DEFAULT 'Customer', 
                        subject TEXT, 
                        message TEXT NOT NULL,
                        admin_response TEXT DEFAULT NULL,
                        timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
                        status TEXT DEFAULT 'Pending'
                    )
                """)
                
               
                columns_to_add = [
                    ("support_tickets", "client_role", "TEXT DEFAULT 'Customer'"),
                    ("support_tickets", "subject", "TEXT"),
                    ("support_tickets", "user_id", "INTEGER")
                ]
                
                for table, col, definition in columns_to_add:
                    try:
                        db_cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
                    except sqlite3.OperationalError:
                        pass 

                
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ticket_replies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticket_id INTEGER NOT NULL,
                        sender TEXT NOT NULL,
                        sender_role TEXT DEFAULT 'Unknown',
                        message TEXT NOT NULL,
                        timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
                    )
                """)

                
                try:
                    db_cursor.execute("ALTER TABLE ticket_replies ADD COLUMN sender_role TEXT DEFAULT 'Unknown'")
                except sqlite3.OperationalError:
                    pass

                # 3. Tabelul pentru chat privat de job (job_messages)
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS job_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id TEXT NOT NULL,
                        sender_id INTEGER NOT NULL,
                        sender_role TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
                    )
                """)
                
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Database creation error: {error}")
            return False

    

    def add_job_message(self, job_id: str, sender_id: int, role: str, message: str) -> bool:
        """Adaugă un mesaj de chat forțând ora locală."""
        try:
            with sqlite3.connect(self.db_path) as connection:
                connection.execute(
                    "INSERT INTO job_messages (job_id, sender_id, sender_role, message, timestamp) VALUES (?, ?, ?, ?, datetime('now', 'localtime'))",
                    (str(job_id), sender_id, role, message)
                )
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Error adding job message: {e}")
            return False

    def get_job_messages(self, job_id: str) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as connection:
                connection.row_factory = sqlite3.Row
                cursor = connection.execute("SELECT * FROM job_messages WHERE job_id = ? ORDER BY timestamp ASC", (str(job_id),))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Error fetching job messages: {e}")
            return []

    

    def insert_ticket(self, client: str, message: str) -> bool:
        """Alias pentru rutele vechi de Customer."""
        return self.create_ticket(user_id=0, client=client, subject="Support Request", message=message, role='Customer')

    def create_ticket(self, user_id: int, client: str, subject: str, message: str, role: str = 'Customer') -> bool:
        """Creează tichetul folosind ora locală pentru sincronizare."""
        try:
            with sqlite3.connect(self.db_path) as connection:
                cursor = connection.cursor()
                cursor.execute("PRAGMA table_info(support_tickets)")
                columns = [col[1] for col in cursor.fetchall()]
                
                initial_status = 'Driver Ticket' if role == 'Driver' else 'Customer Ticket'
                
                if 'client_role' in columns and 'subject' in columns and 'user_id' in columns:
                    connection.execute(
                        "INSERT INTO support_tickets (user_id, client, client_role, subject, message, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))", 
                        (user_id, client, role, subject, message, initial_status)
                    )
                elif 'subject' in columns and 'user_id' in columns:
                    connection.execute(
                        "INSERT INTO support_tickets (user_id, client, subject, message, status, timestamp) VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))", 
                        (user_id, client, subject, message, initial_status)
                    )
                else:
                    connection.execute(
                        "INSERT INTO support_tickets (client, message, status, timestamp) VALUES (?, ?, ?, datetime('now', 'localtime'))", 
                        (client, f"[{subject}] {message}", initial_status)
                    )
                    
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Create ticket error: {e}")
            return False

    def add_reply(self, ticket_id: int, sender: str, message: str, sender_role: str = 'Customer') -> bool:
        """Adaugă o replică cu ora locală și actualizează statusul tichetului."""
        try:
            with sqlite3.connect(self.db_path) as connection:
                cursor = connection.cursor()
                cursor.execute("PRAGMA table_info(ticket_replies)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'sender_role' in columns:
                    connection.execute(
                        "INSERT INTO ticket_replies (ticket_id, sender, sender_role, message, timestamp) VALUES (?, ?, ?, ?, datetime('now', 'localtime'))",
                        (ticket_id, sender, sender_role, message)
                    )
                else:
                    connection.execute(
                        "INSERT INTO ticket_replies (ticket_id, sender, message, timestamp) VALUES (?, ?, ?, datetime('now', 'localtime'))",
                        (ticket_id, sender, message)
                    )
                
               
                if sender_role in ['Staff', 'Administrator']:
                    new_status = 'Answered'
                elif sender_role == 'Driver':
                    new_status = 'Driver Replied'
                else:
                    new_status = 'Customer Replied'
                    
                connection.execute("UPDATE support_tickets SET status = ? WHERE id = ?", (new_status, ticket_id))
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Add reply error: {e}")
            return False

    def get_user_tickets(self, client_username: str) -> List[Dict[str, Any]]:
        """Aduce tichetele pentru un utilizator anume."""
        tickets = []
        try:
            with sqlite3.connect(self.db_path) as connection:
                connection.row_factory = sqlite3.Row
                cursor = connection.execute("SELECT * FROM support_tickets WHERE client = ? ORDER BY id DESC", (client_username,))
                    
                for row in cursor.fetchall():
                    ticket = dict(row)
                    replies_cursor = connection.execute("SELECT * FROM ticket_replies WHERE ticket_id = ? ORDER BY timestamp ASC", (ticket['id'],))
                    ticket['replies'] = [dict(r) for r in replies_cursor.fetchall()]
                    
                    if 'subject' not in ticket or not ticket['subject']:
                        ticket['subject'] = "Support Request"
                        
                    tickets.append(ticket)
                return tickets
        except sqlite3.Error as e:
            logging.error(f"Fetch user tickets error: {e}")
            return tickets

    def get_tickets_by_client(self, client_name: str) -> List[Dict[str, Any]]:
        return self.get_user_tickets(client_name)

    def get_all_tickets(self) -> List[Dict[str, Any]]:
        """Aduce toate tichetele pentru vederea de Admin."""
        tickets = []
        try:
            with sqlite3.connect(self.db_path) as connection:
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

    def delete_ticket(self, ticket_id: int) -> bool:
        try:
            with sqlite3.connect(self.db_path) as connection:
                connection.execute("DELETE FROM support_tickets WHERE id = ?", (ticket_id,))
                connection.execute("DELETE FROM ticket_replies WHERE ticket_id = ?", (ticket_id,))
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Delete error: {e}")
            return False