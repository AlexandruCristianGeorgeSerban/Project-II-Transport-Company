import sqlite3
import logging
from typing import List, Dict, Any

DB_PATH = "instance/database.sqlite"

class DriverPortalModel:
    """Gestioneaza interogarile bazei de date pentru Portalul Soferului."""

    def get_jobs_by_driver(self, driver_name: str) -> List[Dict[str, Any]]:
        """Aduce comenzile alocate soferului, sortate dupa importanta."""
        jobs = []
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM transport_requests 
                    WHERE assigned_driver = ? 
                    ORDER BY 
                        CASE status
                            WHEN 'Accepted' THEN 1
                            WHEN 'In Transit' THEN 2
                            WHEN 'Delivered' THEN 3
                            ELSE 4
                        END
                """, (driver_name,))
                for row in cursor.fetchall():
                    jobs.append(dict(row))
                return jobs
        except sqlite3.Error as e:
            logging.error(f"Eroare la aducerea comenzilor soferului: {e}")
            return jobs

    def update_job_status(self, req_id: str, new_status: str, driver_name: str) -> bool:
        """Actualizeaza statusul comenzii si disponibilitatea soferului."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE transport_requests SET status = ? WHERE id = ? AND assigned_driver = ?", 
                    (new_status, req_id, driver_name)
                )
                
                if new_status == 'Delivered':
                    cursor.execute("UPDATE drivers SET status = 'Available' WHERE name = ?", (driver_name,))
                elif new_status == 'In Transit':
                    cursor.execute("UPDATE drivers SET status = 'Busy' WHERE name = ?", (driver_name,))
                    
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Eroare la actualizarea statusului: {e}")
            return False