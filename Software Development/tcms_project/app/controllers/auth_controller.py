import logging
from datetime import datetime
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
            if calculated_age < MINIMUM_AGE:
                return {"success": False, "message": f"Registration blocked: You must be at least {MINIMUM_AGE} years old."}
                
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

    def authenticate_user(self, username: str, password: str) -> dict:
        """Validates user credentials against the database records."""
        user_db = UserModel()
        # Ne folosim de modelul unificat ca sa facem toata treaba!
        user_record = user_db.verify_login(username, password)

        if user_record:
            return {
                "success": True, 
                "user_id": user_record["id"], 
                "role": user_record["role"],
                "username": user_record["username"],
                "profile_picture": user_record.get("profile_picture") # Extragem si poza direct de aici
            }
        else:
            return {"success": False, "message": "Invalid username or password."}