import sqlite3

def sync_driver_tables():
    try:
        with sqlite3.connect("instance/database.sqlite") as conn:
            cursor = conn.cursor()
            # Adaugam coloanele pentru Alocare in cereri
            try:
                cursor.execute("ALTER TABLE transport_requests ADD COLUMN assigned_driver TEXT DEFAULT NULL")
                cursor.execute("ALTER TABLE transport_requests ADD COLUMN assigned_vehicle TEXT DEFAULT NULL")
            except sqlite3.OperationalError:
                pass # Coloanele exista deja
            
            # Ne asiguram ca avem tabelul de soferi cu Disponibilitate (REQ-23)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drivers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    license_category TEXT NOT NULL,
                    experience_years INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'Available'
                )
            """)
            conn.commit()
            print("✅ Baza de date a fost pregatita pentru portalul Soferului!")
    except Exception as e:
        print(f"❌ Eroare: {e}")

if __name__ == "__main__":
    sync_driver_tables()