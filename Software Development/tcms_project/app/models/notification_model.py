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
        except sqlite3.Error as e:
            logging.error(f"Error creating notifications table: {e}")

    def add_notification(self, target_role: str, message: str) -> bool:
        """Adaugă o alertă pentru un anumit rol (ex: 'Staff', 'Administrator' sau 'All')."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO notifications (target_role, message) VALUES (?, ?)",
                    (target_role, message)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Error adding notification: {e}")
            return False

    def get_unread_notifications(self, role: str) -> List[Dict[str, Any]]:
        """Aduce toate notificările necitite pentru rolul curent."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM notifications WHERE target_role IN (?, 'All') AND is_read = 0 ORDER BY timestamp DESC", 
                    (role,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
            
    def mark_as_read(self, notification_id: int):
        """Marcheaza o notificare ca fiind citita."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error marking notification as read: {e}")