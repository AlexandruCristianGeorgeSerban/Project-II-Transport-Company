import sqlite3
import logging
from typing import List, Dict, Any

DB_PATH = "instance/database.sqlite"

class DriverPortalModel:

    def get_real_driver_id(self, username: str) -> str:
        """
        Face legătura între contul de utilizator și ID-ul real de șofer din Logistică.
        """
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 1. Extragem datele reale ale utilizatorului logat
                user_row = cursor.execute("SELECT first_name, last_name, username FROM users WHERE username = ?", (username,)).fetchone()
                if not user_row:
                    return None
                    
                first = str(user_row['first_name'] or "").strip().lower()
                last = str(user_row['last_name'] or "").strip().lower()
                un = str(user_row['username'] or "").strip().lower()
                
                full_name_1 = f"{first} {last}".strip()
                full_name_2 = f"{last} {first}".strip()
                
                # 2. Căutăm ID-ul corespondent în tabelul de angajați (drivers)
                drivers = cursor.execute("SELECT id, name FROM drivers").fetchall()
                for d in drivers:
                    d_name = str(d['name']).strip().lower()
                    
                    # Dacă numele de utilizator sau prenumele+numele se potrivesc
                    if d_name == full_name_1 or d_name == full_name_2 or d_name == un or un in d_name.replace(" ", ""):
                        return str(d['id'])
                        
        except Exception as e:
            logging.error(f"Eroare DB get_real_driver_id: {e}")
        return None

    def get_jobs(self, driver_id: str, status_type: str = 'active') -> List[Dict[str, Any]]:
        """Aduce comenzile alocate șoferului, fie ele active sau in istoric."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if status_type == 'history':
                    cursor.execute("SELECT * FROM transport_requests WHERE CAST(driver_id AS TEXT) = ? AND status = 'Delivered' ORDER BY id DESC", (driver_id,))
                else:
                    cursor.execute("""
                        SELECT * FROM transport_requests 
                        WHERE CAST(driver_id AS TEXT) = ? AND status IN ('Accepted', 'In Transit')
                        ORDER BY CASE status WHEN 'Accepted' THEN 1 WHEN 'In Transit' THEN 2 ELSE 3 END
                    """, (driver_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Eroare DB get_jobs: {e}")
            return []

    def get_assigned_vehicle(self, driver_id: str) -> Dict[str, Any]:
        """Găsește vehiculul alocat șoferului pe baza unei comenzi active."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT v.* FROM vehicles v
                    JOIN transport_requests tr ON CAST(v.id AS TEXT) = CAST(tr.vehicle_id AS TEXT)
                    WHERE CAST(tr.driver_id AS TEXT) = ? AND tr.status IN ('Accepted', 'In Transit')
                    LIMIT 1
                """, (str(driver_id),))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            return None

    def update_job_status(self, req_id: str, new_status: str) -> bool:
        """Actualizează statusul comenzii și eliberează resursele la finalizare."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE transport_requests SET status = ? WHERE id = ?", (new_status, req_id))
                
                # Când șoferul dă "Finish", eliberăm mașina și șoferul pt următoarea cursă
                if new_status == 'Delivered':
                    cursor.execute("UPDATE vehicles SET status = 'Available' WHERE id IN (SELECT vehicle_id FROM transport_requests WHERE id = ?)", (req_id,))
                    cursor.execute("UPDATE drivers SET status = 'Available', availability = 'Available' WHERE id IN (SELECT driver_id FROM transport_requests WHERE id = ?)", (req_id,))
                    
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Eroare update_job_status: {e}")
            return False

    def update_vehicle_status(self, vehicle_id: str, status: str) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("UPDATE vehicles SET status = ? WHERE id = ?", (status, vehicle_id))
                conn.commit()
                return True
        except sqlite3.Error:
            return False