import logging
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash
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
            dob_date = datetime.strptime(date_of_birth, "%Y-%m-%d")
            today = datetime.today()
            calculated_age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            
            if calculated_age < MINIMUM_AGE:
                return {"success": False, "message": f"Registration blocked: You must be at least {MINIMUM_AGE} years old."}
                
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
        """Validates credentials and enforces a 15-minute lockout after 3 failed attempts."""
        user_db = UserModel()
        user_record = user_db.get_user_for_login(username)

        if not user_record:
            return {"success": False, "message": "Invalid username or password."}

        failed_attempts = user_record.get("failed_attempts") or 0
        lockout_until_str = user_record.get("lockout_until")

        # 1. Verificăm dacă contul este deja blocat
        if lockout_until_str:
            lockout_until = datetime.strptime(lockout_until_str, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < lockout_until:
                remaining_mins = int((lockout_until - datetime.now()).total_seconds() / 60) + 1
                return {"success": False, "message": f"Account locked. Try again in {remaining_mins} minute(s)."}
            else:
                # Blocarea a expirat, îl lăsăm să încerce din nou
                failed_attempts = 0
                user_db.update_lockout(username, 0, None)

        # 2. Verificăm parola
        if check_password_hash(user_record["password_hash"], password):
            # Succes! Ștergem istoricul de greșeli, dacă există
            if failed_attempts > 0:
                user_db.update_lockout(username, 0, None)
                
            return {
                "success": True, 
                "user_id": user_record["id"], 
                "role": user_record["role"],
                "username": user_record["username"],
                "profile_picture": user_record.get("profile_picture")
            }
        else:
            # Parolă greșită!
            failed_attempts += 1
            if failed_attempts >= 3:
                # 3 greșeli atinse -> Pedeapsă de 15 minute
                lockout_time = datetime.now() + timedelta(minutes=15)
                lockout_str = lockout_time.strftime("%Y-%m-%d %H:%M:%S")
                user_db.update_lockout(username, failed_attempts, lockout_str)
                return {"success": False, "message": "Account locked for 15 minutes due to 3 failed attempts."}
            else:
                user_db.update_lockout(username, failed_attempts, None)
                attempts_left = 3 - failed_attempts
                return {"success": False, "message": f"Invalid username or password. {attempts_left} attempt(s) left."}