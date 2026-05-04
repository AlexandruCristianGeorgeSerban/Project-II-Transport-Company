import sqlite3
import logging
from typing import List, Dict, Any

DB_PATH: str = "instance/database.sqlite"

class SupportModel:
    def __init__(self):
        """Inițializează modelul și se asigură că tabelele și coloanele necesare există."""
        self.create_table()

    def create_table(self) -> bool:
        """Creează tabelele și adaugă coloanele noi prin ALTER TABLE dacă este necesar."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                
                # 1. Tabelul principal (support_tickets)
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS support_tickets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER, 
                        client TEXT NOT NULL,
                        client_role TEXT DEFAULT 'Customer', 
                        subject TEXT, 
                        message TEXT NOT NULL,
                        admin_response TEXT DEFAULT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'Pending'
                    )
                """)
                
                # Încercăm să adăugăm coloanele noi în cazul în care tabelul existat deja fără ele
                columns_to_add = [
                    ("support_tickets", "client_role", "TEXT DEFAULT 'Customer'"),
                    ("support_tickets", "subject", "TEXT"),
                    ("support_tickets", "user_id", "INTEGER")
                ]
                
                for table, col, definition in columns_to_add:
                    try:
                        db_cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
                    except sqlite3.OperationalError:
                        pass # Coloana există deja

                # 2. Tabelul pentru replici (ticket_replies)
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ticket_replies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticket_id INTEGER NOT NULL,
                        sender TEXT NOT NULL,
                        sender_role TEXT DEFAULT 'Unknown',
                        message TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Încercăm să adăugăm sender_role dacă lipsește
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
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Database creation error: {error}")
            return False

    # --- FUNCTII PENTRU CHAT PRIVAT (JOB MESSAGES) ---

    def add_job_message(self, job_id: str, sender_id: int, role: str, message: str) -> bool:
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
        """Alias pentru rutele vechi de Customer care trimit doar numele și mesajul."""
        return self.create_ticket(user_id=0, client=client, subject="Customer Request", message=message, role='Customer')

    def create_ticket(self, user_id: int, client: str, subject: str, message: str, role: str = 'Customer') -> bool:
        """Creează tichetul inteligent, adaptându-se la ce coloane există în baza de date."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                cursor = connection.cursor()
                cursor.execute("PRAGMA table_info(support_tickets)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Identificăm statusul inițial în funcție de rol
                initial_status = 'Driver Ticket' if role == 'Driver' else 'Customer Ticket'
                
                # Cazul 1: Tabel complet (Versiunea Nouă)
                if 'client_role' in columns and 'subject' in columns and 'user_id' in columns:
                    connection.execute(
                        "INSERT INTO support_tickets (user_id, client, client_role, subject, message, status) VALUES (?, ?, ?, ?, ?, ?)", 
                        (user_id, client, role, subject, message, initial_status)
                    )
                # Cazul 2: Tabel parțial
                elif 'subject' in columns and 'user_id' in columns:
                    connection.execute(
                        "INSERT INTO support_tickets (user_id, client, subject, message, status) VALUES (?, ?, ?, ?, ?)", 
                        (user_id, client, subject, message, initial_status)
                    )
                # Cazul 3: Tabel vechi (Fallback)
                else:
                    connection.execute(
                        "INSERT INTO support_tickets (client, message, status) VALUES (?, ?, ?)", 
                        (client, f"[{subject}] {message}", initial_status)
                    )
                    
                connection.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Create ticket error: {e}")
            return False

    def add_reply(self, ticket_id: int, sender: str, message: str, sender_role: str = 'Customer') -> bool:
        """Adaugă o replică sigur și actualizează statusul pe baza rolului (Driver/Customer/Staff)."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                cursor = connection.cursor()
                cursor.execute("PRAGMA table_info(ticket_replies)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'sender_role' in columns:
                    connection.execute(
                        "INSERT INTO ticket_replies (ticket_id, sender, sender_role, message) VALUES (?, ?, ?, ?)",
                        (ticket_id, sender, sender_role, message)
                    )
                else:
                    connection.execute(
                        "INSERT INTO ticket_replies (ticket_id, sender, message) VALUES (?, ?, ?)",
                        (ticket_id, sender, message)
                    )
                
                # Actualizăm statusul tichetului principal
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
        """Aduce tichetele pentru un utilizator anume folosind numele de client (username)."""
        tickets = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                cursor = connection.execute("SELECT * FROM support_tickets WHERE client = ? ORDER BY id DESC", (client_username,))
                    
                for row in cursor.fetchall():
                    ticket = dict(row)
                    
                    replies_cursor = connection.execute("SELECT * FROM ticket_replies WHERE ticket_id = ? ORDER BY timestamp ASC", (ticket['id'],))
                    
                    # REPARAȚIA AICI: Lăsăm datele sub formă de listă adevărată, exact cum sunt la admin!
                    ticket['replies'] = [dict(r) for r in replies_cursor.fetchall()]
                    
                    if 'subject' not in ticket or not ticket['subject']:
                        ticket['subject'] = "Support Request"
                        
                    tickets.append(ticket)
                return tickets
        except sqlite3.Error as e:
            logging.error(f"Fetch user tickets error: {e}")
            return tickets

    # Funcția de legătură care rezolvă eroarea ta de la Customer
    def get_tickets_by_client(self, client_name: str) -> List[Dict[str, Any]]:
        """Alias pentru get_user_tickets, ca să nu crape rutele vechi de Customer."""
        return self.get_user_tickets(client_name)

    def get_all_tickets(self) -> List[Dict[str, Any]]:
        """Aduce toate tichetele pentru vederea de Admin."""
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