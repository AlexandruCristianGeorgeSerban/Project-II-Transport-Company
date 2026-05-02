import sqlite3
import logging
from typing import Dict, Any, Optional
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH: str = "instance/database.sqlite"

class UserModel:
    """Handles database operations for user authentication and management."""

    def create_table(self) -> bool:
        """Creates the users table if it does not already exist."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL,
                        first_name TEXT,
                        last_name TEXT,
                        email TEXT UNIQUE,
                        phone_number TEXT,
                        date_of_birth TEXT
                    )
                """)
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Database error during users table creation: {error}")
            return False
        
    def register_user(self, username: str, password: str, first_name: str, last_name: str, email: str, phone_number: str, date_of_birth: str, role: str = "Customer") -> bool:
        """Registers a new user with a hashed password and extended details."""
        try:
            hashed_pw = generate_password_hash(password)
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute(
                    "INSERT INTO users (username, password_hash, role, first_name, last_name, email, phone_number, date_of_birth) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (username, hashed_pw, role, first_name, last_name, email, phone_number, date_of_birth)
                )
                connection.commit()
                return True
        except sqlite3.IntegrityError:
            logging.warning(f"Registration failed: Username '{username}' or Email '{email}' already exists.")
            return False
        except sqlite3.Error as db_error:
            logging.error(f"Insert user error: {db_error}")
            return False

    def verify_login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verifies credentials and returns user details if successful."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT id, username, password_hash, role, first_name, last_name FROM users WHERE username = ?", (username,))
                row = db_cursor.fetchone()
                
                if row is not None:
                    if check_password_hash(row['password_hash'], password):
                        return dict(row)
                    else:
                        return None
                else:
                    return None
        except sqlite3.Error as db_error:
            logging.error(f"Login verification error: {db_error}")
            return None