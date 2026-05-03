import sqlite3
import logging

DB_PATH = "instance/database.sqlite"

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def safe_migrate():
    """Migrează schemele tabelelor fără să șteargă datele existente."""
    logging.info(f"Conectare la baza de date {DB_PATH}...")
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # ==========================================
            # MIGRĂM TABELUL 'users'
            # ==========================================
            logging.info("Începem migrarea pentru tabelul 'users'...")
            
            # 1. Creăm tabelul nou cu structura perfectă
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
            
            # 2. Vedem ce coloane existau în tabelul vechi pentru a ști ce putem copia
            cursor.execute("PRAGMA table_info(users)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            if existing_columns:
                # Coloanele din structura nouă
                target_columns = ['id', 'username', 'password_hash', 'role', 'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'address', 'profile_picture']
                
                # Găsim coloanele comune între tabelul vechi și cel nou
                transfer_columns = [col for col in target_columns if col in existing_columns]
                col_names = ", ".join(transfer_columns)
                
                if col_names:
                    logging.info(f"Copiem datele pentru coloanele: {col_names}")
                    cursor.execute(f"INSERT OR IGNORE INTO users_new ({col_names}) SELECT {col_names} FROM users")
            
                # 3. Ștergem tabelul vechi (stricat)
                cursor.execute("DROP TABLE users")
                
            # 4. Redenumim tabelul nou
            cursor.execute("ALTER TABLE users_new RENAME TO users")
            logging.info("✅ Tabelul 'users' a fost actualizat cu succes, iar datele au fost păstrate!")


            # ==========================================
            # MIGRĂM TABELUL 'transport_requests'
            # ==========================================
            logging.info("Începem migrarea pentru tabelul 'transport_requests'...")
            
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
                    current_lat REAL, 
                    current_lng REAL, 
                    assigned_driver TEXT DEFAULT NULL, 
                    assigned_vehicle TEXT DEFAULT NULL
                )
            """)
            
            cursor.execute("PRAGMA table_info(transport_requests)")
            tr_existing_columns = [col[1] for col in cursor.fetchall()]
            
            if tr_existing_columns:
                tr_target_columns = [
                    'id', 'client', 'cargo_type', 'description', 'weight', 'volume', 'pickup', 'delivery', 
                    'preferred_date', 'status', 'vehicle_id', 'driver_id', 'vehicle_type', 'estimated_price', 
                    'current_lat', 'current_lng', 'assigned_driver', 'assigned_vehicle'
                ]
                
                tr_transfer_columns = [col for col in tr_target_columns if col in tr_existing_columns]
                tr_col_names = ", ".join(tr_transfer_columns)
                
                if tr_col_names:
                    logging.info(f"Copiem datele pentru coloanele: {tr_col_names}")
                    cursor.execute(f"INSERT OR IGNORE INTO transport_requests_new ({tr_col_names}) SELECT {tr_col_names} FROM transport_requests")
                
                cursor.execute("DROP TABLE transport_requests")
                
            cursor.execute("ALTER TABLE transport_requests_new RENAME TO transport_requests")
            logging.info("✅ Tabelul 'transport_requests' a fost actualizat cu succes, iar datele au fost păstrate!")

            conn.commit()
            logging.info("🎉 Toată baza de date a fost migrată în siguranță!")

    except Exception as e:
        logging.error(f"Eroare fatală la migrarea bazei de date: {e}")

if __name__ == "__main__":
    safe_migrate()