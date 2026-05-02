import sqlite3
import os

# Calea către baza ta de date
DB_PATH = "instance/database.sqlite"

def update_database():
    # Ne asigurăm că folderul 'instance' există
    if not os.path.exists('instance'):
        os.makedirs('instance')
        print("Folderul 'instance' a fost creat.")

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    print("Se actualizează structura bazei de date...")

    # Pasul 1: Ștergem tabelul vechi pentru a evita conflictele de coloane
    # Atenție: Acest lucru va șterge utilizatorii creați anterior!
    cursor.execute("DROP TABLE IF EXISTS users")

    # Pasul 2: Creăm tabelul cu TOATE coloanele noi
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone_number TEXT,
            date_of_birth TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()
    print("✅ Succes! Tabelul 'users' a fost recreat cu toate câmpurile necesare:")
    print("   - first_name, last_name, username, email, password_hash, role, phone_number, date_of_birth")

if __name__ == "__main__":
    update_database()