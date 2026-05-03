import sqlite3
import logging
from typing import List, Dict, Any

DB_PATH = "instance/database.sqlite"

class DriverPortalModel:
    """Gestioneaza interogarile bazei de date pentru Portalul Soferului."""

    def get_jobs_by_driver(self, driver_id: str) -> List[Dict[str, Any]]:
        """Aduce comenzile alocate soferului."""
        jobs = []
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Căutăm cursa după ID-ul șoferului
                cursor.execute("""
                    SELECT * FROM transport_requests 
                    WHERE CAST(driver_id AS TEXT) = ? 
                    ORDER BY 
                        CASE status
                            WHEN 'Accepted' THEN 1
                            WHEN 'In Transit' THEN 2
                            WHEN 'Delivered' THEN 3
                            ELSE 4
                        END
                """, (str(driver_id),))
                
                for row in cursor.fetchall():
                    jobs.append(dict(row))
                return jobs
        except sqlite3.Error as e:
            logging.error(f"Eroare la aducerea comenzilor soferului: {e}")
            return jobs

    def update_job_status(self, req_id: str, new_status: str) -> bool:
        """Actualizeaza statusul comenzii."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE transport_requests SET status = ? WHERE id = ?", (new_status, req_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Eroare la actualizarea statusului: {e}")
            return False

    def get_assigned_vehicle(self, driver_id: str) -> Dict[str, Any]:
        """Găsește vehiculul alocat șoferului (pe baza unei comenzi active)."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Căutăm o comandă activă a șoferului pentru a vedea ce mașină conduce
                cursor.execute("""
                    SELECT v.* FROM vehicles v
                    JOIN transport_requests tr ON CAST(v.id AS TEXT) = CAST(tr.vehicle_id AS TEXT)
                    WHERE CAST(tr.driver_id AS TEXT) = ? AND tr.status IN ('Accepted', 'In Transit')
                    LIMIT 1
                """, (str(driver_id),))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except sqlite3.Error as e:
            logging.error(f"Eroare la găsirea vehiculului alocat: {e}")
            return None