import sqlite3
import logging

DB_PATH: str = "instance/database.sqlite"

class UserModel:
    """Handles direct database initialization and structures for users."""

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
                        date_of_birth TEXT
                    )
                """)
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Database error during table creation: {error}")
            return False