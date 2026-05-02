import sqlite3
import logging
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH: str = "instance/database.sqlite"
MINIMUM_AGE: int = 13

class AuthController:
    """Manages authentication business logic, registration, and age validation."""

    def register_customer(self, username: str, password: str, date_of_birth: str) -> dict:
        """Registers a new customer if they meet the minimum age requirement."""
        try:
            dob_date = datetime.strptime(date_of_birth, "%Y-%m-%d")
            today = datetime.today()
            calculated_age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            
            if calculated_age < MINIMUM_AGE:
                return {"success": False, "message": "Registration blocked: You must be at least 13 years old."}
            else:
                hashed_password = generate_password_hash(password)
                return self._insert_user(username, hashed_password, "Customer", date_of_birth)
        except ValueError as val_error:
            logging.error(f"Date parsing error: {val_error}")
            return {"success": False, "message": "Invalid date format provided."}

    def _insert_user(self, username: str, hashed_pw: str, role: str, dob: str) -> dict:
        """Executes the safe SQL insertion for a new user."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute(
                    "INSERT INTO users (username, password_hash, role, date_of_birth) VALUES (?, ?, ?, ?)",
                    (username, hashed_pw, role, dob)
                )
                connection.commit()
                return {"success": True, "message": "Account created successfully. You can now log in."}
        except sqlite3.IntegrityError as integrity_error:
            logging.error(f"Integrity error (Duplicate User): {integrity_error}")
            return {"success": False, "message": "Username is already taken."}
        except sqlite3.Error as db_error:
            logging.error(f"Database insertion error: {db_error}")
            return {"success": False, "message": "Internal database error occurred."}

    def authenticate_user(self, username: str, password: str) -> dict:
        """Validates user credentials against the database records."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                
                # MODIFICAREA 1: Am adăugat profile_picture în SELECT
                db_cursor.execute(
                    "SELECT id, username, password_hash, role, profile_picture FROM users WHERE username = ?", 
                    (username,)
                )
                user_record = db_cursor.fetchone()

                if user_record is None:
                    return {"success": False, "message": "Invalid username or password."}
                elif check_password_hash(user_record["password_hash"], password):
                    # MODIFICAREA 2: Returnăm și profile_picture în dicționar
                    return {
                        "success": True, 
                        "user_id": user_record["id"], 
                        "role": user_record["role"],
                        "username": user_record["username"],
                        "profile_picture": user_record["profile_picture"]
                    }
                else:
                    return {"success": False, "message": "Invalid username or password."}
        except sqlite3.Error as error:
            logging.error(f"Database read error: {error}")
            return {"success": False, "message": "Internal database error occurred."}