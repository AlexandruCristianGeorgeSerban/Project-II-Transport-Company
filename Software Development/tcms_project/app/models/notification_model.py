import sqlite3
import logging
from typing import List, Dict, Any

DB_PATH = "instance/database.sqlite"

class NotificationModel:
    def create_table(self):
        """Creeaza tabelul de notificari daca nu exista."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target_role TEXT NOT NULL,
                        message TEXT NOT NULL,
                        is_read INTEGER DEFAULT 0,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                
                # 🔴 REPARAȚIE SIGURĂ: Verificăm dacă există coloana, iar dacă nu, o punem.
                cursor = conn.execute("PRAGMA table_info(notifications)")
                columns = [info[1] for row in cursor.fetchall() for info in [row]]
                if 'target_url' not in columns:
                    conn.execute("ALTER TABLE notifications ADD COLUMN target_url TEXT DEFAULT ''")
                    conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error creating notifications table: {e}")

    # 🔴 AM ADAUGAT target_url CA PARAMETRU OPTIONAL
    def add_notification(self, target_role: str, message: str, target_url: str = "") -> bool:
        """Adaugă o alertă cu ora sincronizată perfect."""
        self.create_table() # Ne asigurăm că baza de date este actualizată
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO notifications (target_role, message, target_url, timestamp) VALUES (?, ?, ?, datetime('now', 'localtime'))",
                    (str(target_role).strip(), message, target_url)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Error adding notification: {e}")
            return False

    def get_unread_notifications(self, target1: str, target2: str = '') -> List[Dict[str, Any]]:
        """Aduce notificările pentru Username-ul specific, pentru Rolul său sau pentru 'All'."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM notifications WHERE target_role IN (?, ?, 'All') AND is_read = 0 ORDER BY timestamp DESC", 
                    (str(target1).strip(), str(target2).strip())
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Error fetching notifications: {e}")
            return []
            
    def mark_as_read(self, notification_id: int):
        """Marcheaza o notificare ca fiind citita."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error marking notification as read: {e}") 
            
   # 🔴 NOU: FUNCTIE CA SA EXTRAGEM LINKUL CAND CINEVA DA CLICK
    def get_notification_url(self, notification_id: int) -> str:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT target_url FROM notifications WHERE id = ?", (notification_id,)).fetchone()
                
                # REPARAȚIA E AICI: Transformăm rândul într-un dicționar pur ca să extragem fără probleme
                if row:
                    row_dict = dict(row)
                    if 'target_url' in row_dict and row_dict['target_url']:
                        return row_dict['target_url']
        except sqlite3.Error as e:
            logging.error(f"Eroare extragere link notificare: {e}")
        return ""