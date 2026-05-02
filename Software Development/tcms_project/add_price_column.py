import sqlite3
import os

# Setăm calea către baza de date
db_path = os.path.join(os.getcwd(), "instance", "database.sqlite")

def setup_requests_table():
    print(f"🔍 Mă conectez la baza de date: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ EROARE: Nu găsesc baza de date.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Creăm tabelul requests cu absolut toate coloanele necesare!
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY,
                client TEXT NOT NULL,
                cargo_type TEXT NOT NULL,
                description TEXT,
                weight REAL,
                volume REAL,
                pickup TEXT NOT NULL,
                delivery TEXT NOT NULL,
                preferred_date TEXT,
                status TEXT DEFAULT 'Pending',
                price REAL DEFAULT 0.0
            )
        """)
        
        conn.commit()
        print("✅ SUCCES! Tabelul 'requests' a fost creat și conține coloana de preț.")
        
    except Exception as e:
        print(f"❌ Eroare neașteptată: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_requests_table()