import sqlite3
import os

DB_PATH = "instance/database.sqlite"

def update_database():
    if not os.path.exists('instance'):
        os.makedirs('instance')

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    print("Se actualizează structura bazei de date...")

    cursor.execute("DROP TABLE IF EXISTS users")

    # AM ADAUGAT COLOANELE LIPSĂ LA FINAL: address și profile_picture
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
            date_of_birth TEXT NOT NULL,
            address TEXT,
            profile_picture TEXT
        )
    """)

    connection.commit()
    connection.close()
    print("✅ Succes! Tabelul 'users' are acum si address, si profile_picture!")

if __name__ == "__main__":
    update_database()