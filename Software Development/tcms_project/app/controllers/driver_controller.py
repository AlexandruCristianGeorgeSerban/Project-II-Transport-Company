import logging
from typing import Dict, Any
from app.models.driver_model import DriverModel
from app.models.user_model import UserModel
from app.controllers.log_controller import LogController
import sqlite3

class DriverController:
    """Processes business logic and formats data for Driver Management."""

    def __init__(self) -> None:
        """Initializes the model and creates the table."""
        self.model = DriverModel()
        self.model.create_table()
        self.user_model = UserModel()
        
        self.logger = LogController()

    def load_driver_data(self) -> Dict[str, Any]:
        """Loads and structures all necessary driver data."""
        driver_data: Dict[str, Any] = {}
        try:
            driver_data["summary"] = self.model.get_driver_summary()
            driver_data["drivers"] = self.model.get_all_drivers()
            return driver_data
        except Exception as logic_error:
            logging.error(f"Error processing driver data: {logic_error}")
            driver_data["summary"] = {"total": 0, "active": 0, "on_leave": 0}
            driver_data["drivers"] = []
            return driver_data

    # 🔴 Aici am reparat! Am adăugat 'email: str = None' în listă, exact la locul potrivit
    def add_new_driver(self, d_id: str, name: str, status: str, licenses: str, exp: str, dob: str, address: str, avail: str, email: str = None, username: str = None, password: str = None, modified_by: str = "System") -> dict:
        """Handles logic for adding a new driver and automatically creates an account."""
        
        full_name = str(name).strip() if name else "Unknown"
        
        if username and password:
            # Spargem automat în două ca să-i facă userul
            name_parts = full_name.split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            # Trimitem datele (inclusiv email-ul) spre baza de date de login
            account_created = self.user_model.register_user(
                username=username, 
                password=password, 
                first_name=first_name, 
                last_name=last_name,
                email=email, 
                phone_number=None,
                date_of_birth=dob,
                role="Driver",
                address=address
            )
            
            if not account_created:
                return {"success": False, "message": f"Error: The username '{username}' or email '{email}' is already taken."}

        # Salvăm numele întreg exact cum a fost scris în logistică
        result = self.model.insert_driver(d_id, full_name, status, licenses, exp, dob, address, avail)
        
        if result is True:
            self.logger.log_action("CREATE", "Driver", d_id, modified_by, f"Added new driver profile: {full_name}")
            return {"success": True, "message": f"Driver {full_name} added successfully!"}
        else:
            return {"success": False, "message": "Error: Driver ID or Data might already exist."}

    def modify_driver(self, d_id: str, name: str, status: str, licenses: str, exp: str, dob: str, address: str, avail: str, modified_by: str = "System") -> dict:
        """Handles logic for updating a driver."""
        full_name = str(name).strip() if name else "Unknown"
        
        result = self.model.update_driver(d_id, full_name, status, licenses, exp, dob, address, avail, modified_by)
        
        if result is True:
            log_details = f"Name: {full_name} | Status: {status} | Avail: {avail} | Lic: {licenses}"
            self.logger.log_action("UPDATE", "Driver", d_id, modified_by, log_details)
            
            return {"success": True, "message": f"Driver {full_name} updated successfully!"}
        else:
            return {"success": False, "message": "Error updating driver."}

    def remove_driver(self, d_id: str, modified_by: str = "System") -> dict:
        """Handles logic for removing a driver AND their associated user account."""
        
        # 1. Găsim și ștergem CONTUL DE UTILIZATOR asociat acestui șofer
        try:
            with sqlite3.connect("instance/database.sqlite") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                target_username = None
                
                # Căutăm întâi după ID
                cursor.execute("SELECT username FROM users WHERE role = 'Driver' AND CAST(id AS TEXT) = ?", (str(d_id),))
                row = cursor.fetchone()
                if row:
                    target_username = row['username']
                else:
                    # Dacă nu dă roade, căutăm după Numele curățat
                    cursor.execute("SELECT name FROM drivers WHERE id = ?", (d_id,))
                    d_row = cursor.fetchone()
                    if d_row:
                        d_name = str(d_row[0]).lower().strip().replace(" ", "")
                        cursor.execute("SELECT username, first_name, last_name FROM users WHERE role = 'Driver'")
                        for u in cursor.fetchall():
                            u_un = str(u[0]).lower().strip()
                            u_f1 = f"{str(u[1] or '')}{str(u[2] or '')}".lower().replace(" ", "")
                            u_f2 = f"{str(u[2] or '')}{str(u[1] or '')}".lower().replace(" ", "")
                            
                            if d_name == u_un or d_name == u_f1 or d_name == u_f2:
                                target_username = u[0]
                                break
                
                # Avem username-ul? Îl ștergem din tabelul users.
                if target_username:
                    cursor.execute("DELETE FROM users WHERE username = ?", (target_username,))
                    conn.commit()
                    logging.warning(f"[DELETE DRIVER] Contul de logare '{target_username}' a fost șters complet!")
                    
        except Exception as e:
            logging.error(f"[DELETE DRIVER] Eroare la ștergerea contului de user: {e}")

        # 2. Ștergem dosarul șoferului din tabelul de Logistică (drivers)
        result = self.model.delete_driver(d_id)
        
        if result is True:
            self.logger.log_action("DELETE", "Driver", d_id, modified_by, "Deleted driver from database")
            return {"success": True, "message": "Driver and associated account deleted successfully!"}
        else:
            return {"success": False, "message": "Error deleting driver."}