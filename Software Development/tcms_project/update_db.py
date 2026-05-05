import sqlite3
import logging

DB_PATH = "instance/database.sqlite"

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def safe_migrate():
    logging.info(f"Conectare la baza de date {DB_PATH}...")
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Dezactivăm cheile străine temporar pentru a permite DROP/RENAME
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # ==========================================
            # 1. MIGRĂM TABELUL 'users'
            # ==========================================
            logging.info("Migrare 'users'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    email TEXT UNIQUE,
                    phone_number TEXT,
                    date_of_birth TEXT,
                    address TEXT,
                    profile_picture TEXT
                )
            """)
            
            cursor.execute("PRAGMA table_info(users)")
            cols = [c[1] for c in cursor.fetchall()]
            if cols:
                target = ['id', 'username', 'password_hash', 'role', 'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'address', 'profile_picture']
                common = ", ".join([c for c in target if c in cols])
                cursor.execute(f"INSERT OR IGNORE INTO users_new ({common}) SELECT {common} FROM users")
                cursor.execute("DROP TABLE users")
            cursor.execute("ALTER TABLE users_new RENAME TO users")

            # ==========================================
            # 2. MIGRĂM TABELUL 'transport_requests' (Fix Price Offer)
            # ==========================================
            logging.info("Migrare 'transport_requests'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transport_requests_new (
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
                    vehicle_id TEXT, 
                    driver_id TEXT, 
                    vehicle_type TEXT, 
                    estimated_price REAL,
                    price_offer REAL, 
                    current_lat REAL, 
                    current_lng REAL
                )
            """)
            
            cursor.execute("PRAGMA table_info(transport_requests)")
            cols = [c[1] for c in cursor.fetchall()]
            if cols:
                target = ['id', 'client', 'cargo_type', 'description', 'weight', 'volume', 'pickup', 'delivery', 'preferred_date', 'status', 'vehicle_id', 'driver_id', 'vehicle_type', 'estimated_price', 'price_offer', 'current_lat', 'current_lng']
                # Verificăm dacă există date vechi în 'assigned_driver' să le mapăm pe 'driver_id' dacă e cazul
                mapping = {c: c for c in target if c in cols}
                if 'assigned_driver' in cols and 'driver_id' not in cols: mapping['driver_id'] = 'assigned_driver'
                if 'assigned_vehicle' in cols and 'vehicle_id' not in cols: mapping['vehicle_id'] = 'assigned_vehicle'
                
                select_cols = ", ".join(mapping.values())
                insert_cols = ", ".join(mapping.keys())
                
                cursor.execute(f"INSERT OR IGNORE INTO transport_requests_new ({insert_cols}) SELECT {select_cols} FROM transport_requests")
                cursor.execute("DROP TABLE transport_requests")
            cursor.execute("ALTER TABLE transport_requests_new RENAME TO transport_requests")

            # ==========================================
            # 3. ASIGURĂM EXISTENȚA TABELELOR 'drivers' ȘI 'vehicles'
            # ==========================================
            # Acestea sunt necesare pentru rapoartele de Analytics
            logging.info("Verificare tabele suport (drivers/vehicles)...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drivers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    licenses TEXT,
                    availability TEXT DEFAULT 'Available',
                    status TEXT DEFAULT 'Active',
                    user_id INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plate_number TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    capacity REAL,
                    status TEXT DEFAULT 'Active'
                )
            """)

            # Reactivăm cheile străine
            cursor.execute("PRAGMA foreign_keys = ON")
            conn.commit()
            logging.info("🎉 Migrare finalizată cu succes!")

    except Exception as e:
        logging.error(f"Eroare fatală la migrarea bazei de date: {e}")

if __name__ == "__main__":
    safe_migrate()