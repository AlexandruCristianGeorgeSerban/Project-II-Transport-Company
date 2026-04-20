import sqlite3
import time
import random

DB_PATH = "instance/database.sqlite"

def simulate_gps():
    print("📡 Pornire modul GPS Simulator... (Apasa CTRL+C pentru a opri)")
    
    while True:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                # Cautam toate cursele aflate pe drum
                cursor.execute("SELECT id, current_lat, current_lng FROM transport_requests WHERE status = 'In Transit'")
                active_jobs = cursor.fetchall()
                
                if not active_jobs:
                    print("...Nicio cursa pe drum in acest moment...")
                
                for job in active_jobs:
                    req_id, lat, lng = job
                    
                    # Daca cursa abia a inceput, o punem in centrul tarii (sau orasul de plecare)
                    if lat is None or lng is None:
                        # Coordonate random de inceput (Bucuresti aproximativ)
                        lat, lng = 44.4268, 26.1025
                    
                    # SIMULAM MISCAREA: Modificam usor latitudinea si longitudinea (ca si cum ar conduce)
                    new_lat = lat + random.uniform(-0.01, 0.01)
                    new_lng = lng + random.uniform(-0.01, 0.01)
                    
                    # Salvam noile coordonate in BAZA DE DATE
                    cursor.execute("UPDATE transport_requests SET current_lat = ?, current_lng = ? WHERE id = ?", (new_lat, new_lng, req_id))
                    print(f"🚚 Cursa {req_id} s-a mutat la coordonatele: [{new_lat:.4f}, {new_lng:.4f}]")
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            
        # Asteptam 3 secunde inainte sa trimitem urmatorul "semnal GPS"
        time.sleep(3)

if __name__ == "__main__":
    simulate_gps()