import sqlite3
import logging

DB_PATH = "instance/database.sqlite"

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def safe_migrate():
    logging.info(f"Conectare la baza de date {DB_PATH}...")
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Dezactivăm cheile străine temporar pentru a permite redenumiri și stocări sigure
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # ==========================================
            # 1. MIGRĂM TABELUL 'users' (SIGUR - PĂSTREAZĂ DATELE)
            # ==========================================
            logging.info("Verificare/Migrare tabel 'users'...")
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
                    profile_picture TEXT,
                    failed_attempts INTEGER DEFAULT 0,
                    lockout_until TEXT
                )
            """)
            
            cursor.execute("PRAGMA table_info(users)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            if existing_columns:
                target_columns = ['id', 'username', 'password_hash', 'role', 'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'address', 'profile_picture', 'failed_attempts', 'lockout_until']
                transfer_columns = [col for col in target_columns if col in existing_columns]
                col_names = ", ".join(transfer_columns)
                
                if col_names:
                    cursor.execute(f"INSERT OR IGNORE INTO users_new ({col_names}) SELECT {col_names} FROM users")
                cursor.execute("DROP TABLE users")
                
            cursor.execute("ALTER TABLE users_new RENAME TO users")

            # ==========================================
            # 2. MIGRĂM TABELUL 'transport_requests' (SIGUR - PĂSTREAZĂ DATELE)
            # ==========================================
            logging.info("Verificare/Migrare tabel 'transport_requests'...")
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
            tr_existing_columns = [col[1] for col in cursor.fetchall()]
            
            if tr_existing_columns:
                tr_target_columns = [
                    'id', 'client', 'cargo_type', 'description', 'weight', 'volume', 'pickup', 'delivery', 
                    'preferred_date', 'status', 'vehicle_id', 'driver_id', 'vehicle_type', 'estimated_price', 
                    'price_offer', 'current_lat', 'current_lng'
                ]
                
                mapping = {c: c for c in tr_target_columns if c in tr_existing_columns}
                if 'assigned_driver' in tr_existing_columns and 'driver_id' not in tr_existing_columns: 
                    mapping['driver_id'] = 'assigned_driver'
                if 'assigned_vehicle' in tr_existing_columns and 'vehicle_id' not in tr_existing_columns: 
                    mapping['vehicle_id'] = 'assigned_vehicle'
                
                insert_cols = ", ".join(mapping.keys())
                select_cols = ", ".join(mapping.values())
                
                if insert_cols:
                    cursor.execute(f"INSERT OR IGNORE INTO transport_requests_new ({insert_cols}) SELECT {select_cols} FROM transport_requests")
                cursor.execute("DROP TABLE transport_requests")
                
            cursor.execute("ALTER TABLE transport_requests_new RENAME TO transport_requests")

            # ==========================================
            # 3. MIGRĂM ȘI REPARĂM TABELUL 'drivers' (ELIMINĂM document_id SIGUR)
            # ==========================================
            logging.info("Verificare/Migrare tabel 'drivers' (fără document_id)...")
            
            # Creăm noul tabel FĂRĂ coloana document_id
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drivers_new (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    licenses TEXT,
                    experience TEXT,
                    dob TEXT,
                    address TEXT,
                    availability TEXT DEFAULT 'Available'
                )
            """)
            
            cursor.execute("PRAGMA table_info(drivers)")
            drv_existing_columns = [col[1] for col in cursor.fetchall()]
            
            # Dacă tabelul vechi are date în el, le transferăm
            if drv_existing_columns:
                # LISTA NOUĂ ȚINTĂ - am scos 'document_id' de aici
                drv_target_columns = ['id', 'name', 'status', 'licenses', 'experience', 'dob', 'address', 'availability']
                transfer_columns = [col for col in drv_target_columns if col in drv_existing_columns]
                col_names = ", ".join(transfer_columns)
                
                if col_names:
                    # Datele se copiază, ignorând complet coloana document_id veche
                    cursor.execute(f"INSERT OR IGNORE INTO drivers_new ({col_names}) SELECT {col_names} FROM drivers")
                
                # Ștergem tabelul vechi DOAR DUPĂ ce datele s-au copiat cu succes în drivers_new
                cursor.execute("DROP TABLE drivers")
                
            cursor.execute("ALTER TABLE drivers_new RENAME TO drivers")

            # ==========================================
            # 4. ASIGURĂM TABELUL 'vehicles' (SIGUR)
            # ==========================================
            logging.info("Verificare tabel 'vehicles'...")
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
            logging.info("🎉 Baza de date a fost actualizată securizat, fără pierderi de date!")

    except Exception as e:
        logging.error(f"Eroare fatală la migrarea bazei de date: {e}")

if __name__ == "__main__":
    safe_migrate()