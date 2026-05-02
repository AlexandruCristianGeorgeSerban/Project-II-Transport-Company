import sqlite3
import logging
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from app.models.user_model import UserModel

DB_PATH: str = "instance/database.sqlite"
MINIMUM_AGE: int = 13

class AuthController:
    """Manages authentication business logic, registration, and age validation."""

    def register_customer(self, username, password, first_name, last_name, email, phone_number, date_of_birth) -> dict:
        """Registers a new customer if they meet the minimum age requirement."""
        user_db = UserModel()
        user_db.create_table() # Ne asigurăm că tabelul există
        
        try:
            # 1. Calculăm vârsta
            dob_date = datetime.strptime(date_of_birth, "%Y-%m-%d")
            today = datetime.today()
            calculated_age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            
            # 2. Verificăm vârsta
            if calculated_age < 13: # Am pus 13 direct aici ca să nu ne mai complicăm cu variabile globale
                return {"success": False, "message": "Registration blocked: You must be at least 13 years old."}
                
            # 3. Trimitem TOT la baza de date
            success = user_db.register_user(
                username=username, 
                password=password, 
                first_name=first_name, 
                last_name=last_name, 
                email=email, 
                phone_number=phone_number, 
                date_of_birth=date_of_birth, 
                role="Customer"
            )
            
            if success:
                 return {"success": True, "message": "Account created successfully! You can now login."}
            else:
                 return {"success": False, "message": "Registration failed. Username or email might already exist."}

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
                db_cursor.execute(
                    "SELECT id, username, password_hash, role FROM users WHERE username = ?", 
                    (username,)
                )
                user_record = db_cursor.fetchone()

                if user_record is None:
                    return {"success": False, "message": "Invalid username or password."}
                elif check_password_hash(user_record["password_hash"], password):
                    return {
                        "success": True, 
                        "user_id": user_record["id"], 
                        "role": user_record["role"],
                        "username": user_record["username"]
                    }
                else:
                    return {"success": False, "message": "Invalid username or password."}
        except sqlite3.Error as error:
            logging.error(f"Database read error: {error}")
            return {"success": False, "message": "Internal database error occurred."}