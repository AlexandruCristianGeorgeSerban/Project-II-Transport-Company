import sqlite3
import logging
from typing import List, Dict, Any

DB_PATH = "instance/database.sqlite"

class LogModel:
    """Gestionează interogările pentru Audit Trail (System Logs)"""
    
    def add_log(self, action_type: str, target_entity: str, target_id: str, performed_by: str, details: str) -> bool:
        """Adaugă o intrare nouă în istoricul sistemului."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_logs (action_type, target_entity, target_id, performed_by, details)
                    VALUES (?, ?, ?, ?, ?)
                """, (action_type, target_entity, target_id, performed_by, details))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Eroare adăugare log: {e}")
            return False

    def get_all_logs(self) -> List[Dict[str, Any]]:
        """Aduce toate logurile, cele mai noi primele."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM system_logs ORDER BY timestamp DESC")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Eroare citire loguri: {e}")
            return []