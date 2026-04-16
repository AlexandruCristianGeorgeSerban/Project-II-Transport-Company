import sqlite3

DB_PATH = "instance/database.sqlite"

def fix_database():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 1. Recreăm tabelul de cereri cu TOATE cele 12 coloane
            cursor.execute("DROP TABLE IF EXISTS transport_requests")
            cursor.execute("""
                CREATE TABLE transport_requests (
                    id TEXT PRIMARY KEY,
                    client TEXT NOT NULL,
                    cargo_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    weight REAL NOT NULL,
                    volume REAL NOT NULL,
                    pickup TEXT NOT NULL,
                    delivery TEXT NOT NULL,
                    preferred_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    vehicle_type TEXT,
                    price_offer REAL
                )
            """)
            
            # 2. Creăm noul tabel pentru Support Tickets
            cursor.execute("DROP TABLE IF EXISTS support_tickets")
            cursor.execute("""
                CREATE TABLE support_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'New'
                )
            """)
            
            conn.commit()
            print("✅ Baza de date a fost reparată și curățată!")
    except Exception as e:
        print(f"❌ Eroare la reparare: {e}")

if __name__ == "__main__":
    fix_database()