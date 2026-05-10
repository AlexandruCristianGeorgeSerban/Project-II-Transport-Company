import logging
from typing import Dict, Any
from app.models.allocation_model import AllocationModel
from app.models.invoice_model import InvoiceModel
from app.models.notification_model import NotificationModel
from app.models.log_model import LogModel  
from datetime import datetime
import uuid
import sqlite3

def check_license_compatibility(driver_licenses: str, vehicle_type: str) -> bool:
    if not driver_licenses or not vehicle_type:
        return False
    
    rules = {
        "Van": ["B", "C", "CE"],
        "Truck": ["C", "CE"],
        "Lorrie": ["C", "CE"],
        "Semi-Trailer": ["CE"],
        "TIR": ["CE"],
        "Airplane": ["Pilot (ATPL)", "Pilot", "Pilot (Airplane)"],
        "Ship": ["Maritime", "Maritime (Ship)"],
        "Train": ["Train Operator", "Train"]
    }

    driver_has = [lic.strip() for lic in driver_licenses.split(',')]
    allowed_licenses = rules.get(vehicle_type, [])

    for lic in driver_has:
        if lic in allowed_licenses:
            return True 
    return False

class AllocationController:
    def __init__(self) -> None:
        self.model = AllocationModel()
        self.log_db = LogModel()

    def _find_driver_username(self, driver_id_str: str) -> str:
        """Funcția DETECTIV plină de log-uri masive pentru a găsi corect șoferul."""
        logging.warning(f"==================================================")
        logging.warning(f"[DETECTIV ȘOFER] Start căutare username pentru driver_id: '{driver_id_str}'")
        target_username = None
        
        try:
            with sqlite3.connect("instance/database.sqlite") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Pasul 1: Găsim numele șoferului din logistică
                cursor.execute("SELECT name FROM drivers WHERE CAST(id AS TEXT) = ?", (driver_id_str,))
                d_row = cursor.fetchone()
                
                if not d_row:
                    logging.warning(f"[DETECTIV ȘOFER] EȘEC: Nu există angajat cu id-ul '{driver_id_str}' în tabelul 'drivers'!")
                    return None
                    
                d_name = str(d_row['name']).strip()
                d_name_clean = d_name.lower().replace(" ", "")
                logging.warning(f"[DETECTIV ȘOFER] Angajatul găsit în logistică este: '{d_name}' (Sintaxă curată: '{d_name_clean}')")
                
                # Pasul 2: Căutăm doar printre utilizatorii care chiar sunt Driveri! (ignorăm Clientul "22")
                cursor.execute("SELECT id, username, first_name, last_name FROM users WHERE role = 'Driver'")
                users = cursor.fetchall()
                logging.warning(f"[DETECTIV ȘOFER] Analizăm {len(users)} conturi de tip 'Driver' din sistem pentru potrivire...")
                
                for u in users:
                    u_id = str(u['id']).strip()
                    u_un = str(u['username']).strip().lower()
                    u_f1 = f"{u['first_name'] or ''}{u['last_name'] or ''}".strip().lower().replace(" ", "")
                    u_f2 = f"{u['last_name'] or ''}{u['first_name'] or ''}".strip().lower().replace(" ", "")
                    
                    logging.warning(f"  -> Verificăm contul Driver: ID={u_id}, Username='{u_un}', Nume='{u_f1}'")
                    
                    # Verificăm dacă i se potrivește ID-ul
                    if u_id == driver_id_str:
                        logging.warning(f"  [!!!] MATCH PERFECT pe ID de cont ({u_id})! Acesta este șoferul.")
                        target_username = str(u['username'])
                        break
                        
                    # Verificăm dacă username-ul seamănă cu numele lui (ex: "ship" se potrivește cu "Ship Driver")
                    if u_un == d_name_clean or (len(u_un) > 2 and u_un in d_name_clean) or (len(d_name_clean) > 2 and d_name_clean in u_un):
                        logging.warning(f"  [!!!] MATCH pe Username ('{u_un}' a fost recunoscut în '{d_name_clean}')!")
                        target_username = str(u['username'])
                        break
                        
                    # Verificăm dacă numele din cont seamănă cu numele din logistică
                    if (u_f1 and u_f1 in d_name_clean) or (u_f2 and u_f2 in d_name_clean):
                        logging.warning(f"  [!!!] MATCH pe Numele Real ('{u_f1}' recunoscut în '{d_name_clean}')!")
                        target_username = str(u['username'])
                        break
                        
        except Exception as e:
            logging.error(f"[DETECTIV ȘOFER] Eroare SQL gravă: {e}")
            
        if target_username:
            logging.warning(f"[DETECTIV ȘOFER] SUCCES! Șoferul găsit este -> '{target_username}' <- Trimitem notificarea lui!")
        else:
            logging.warning(f"[DETECTIV ȘOFER] EȘEC TOTAL! Nu s-a putut asocia driver_id '{driver_id_str}' cu niciun cont 'Driver'! Notificarea va fi ANULATĂ ca să nu se ducă la altcineva.")
        logging.warning(f"==================================================")
            
        return target_username

    def load_allocation_data(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        try:
            data["requests"] = self.model.get_pending_requests()
            data["vehicles"] = self.model.get_available_vehicles()
            data["drivers"] = self.model.get_available_drivers()
            return data
        except Exception as error:
            logging.error(f"Logic error loading allocation data: {error}")
            return {"requests": [], "vehicles": [], "drivers": []}

    def process_allocation(self, req_id: str, veh_id: str, drv_id: str, staff_username: str = "Unknown") -> dict:
        if not req_id or not veh_id or not drv_id:
            return {"success": False, "message": "Please select a Request, a Vehicle, and a Driver!"}

        try:
            constraints = self.model.get_allocation_constraints(req_id, veh_id, drv_id)
            
            if constraints and "weight" in constraints and "capacity" in constraints:
                if constraints["weight"] > constraints["capacity"]:
                    return {
                        "success": False, 
                        "message": f"❌ Eroare REQ-46: Capacitatea ({constraints['capacity']}) < Marfă ({constraints['weight']})!"
                    }
                    
            if constraints and "driver_licenses" in constraints and "vehicle_type" in constraints:
                if not check_license_compatibility(constraints["driver_licenses"], constraints["vehicle_type"]):
                    return {
                        "success": False,
                        "message": f"❌ Eroare Permis: Șoferul nu poate conduce {constraints['vehicle_type']}!"
                    }

            result = self.model.allocate_resources(req_id, veh_id, drv_id, staff_username)
            if result is True:
                self.log_db.add_log(
                    action_type="UPDATE",
                    target_entity="Transport Request",
                    target_id=req_id,
                    performed_by=staff_username,
                    details=f"Assigned Vehicle '{veh_id}' and Driver '{drv_id}' to the order."
                )
                
                # --- START NOTIFICĂRI ALOCARE ---
                notif_model = NotificationModel()
                notif_model.add_notification("Staff", f"🚚 Alocare finalizată! Cererea {req_id} a plecat la drum.", target_url="/active_jobs")
                
                # Aici apelăm Detectivul!
                target_driver_username = self._find_driver_username(str(drv_id))
                
                if target_driver_username:
                    notif_model.add_notification(
                        target_driver_username, 
                        f"📍 Ți-a fost alocată cursa nouă {req_id}. Drum bun!",
                        target_url="/driver/portal"
                    )
                # --- END NOTIFICĂRI ALOCARE ---
                
                return {"success": True, "message": f"Successfully allocated Vehicle {veh_id} and Driver {drv_id} to Request {req_id}!"}
            else:
                return {"success": False, "message": "An error occurred during allocation."}
                
        except Exception as e:
            logging.error(f"Eroare la procesarea alocării: {e}")
            return {"success": False, "message": "A apărut o eroare internă la alocare."}
        
    def load_active_jobs(self, role: str = 'Staff', driver_id: str = None) -> dict:
        try:
            all_jobs = self.model.get_active_jobs()
            if role == 'Driver' and driver_id:
                my_jobs = [job for job in all_jobs if str(job.get('driver_id')) == str(driver_id)]
                return {"jobs": my_jobs}
            return {"jobs": all_jobs}
        except Exception as e:
            return {"jobs": []}

    def complete_active_job(self, req_id: str) -> dict:
        try:
            with sqlite3.connect("instance/database.sqlite") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM transport_requests WHERE id = ?", (req_id,))
                req_data = cursor.fetchone()
        except Exception as e:
            return {"success": False, "message": "Database error."}

        if not req_data:
            return {"success": False, "message": "Cererea nu a fost găsită."}

        client_name = req_data['client']
        drv_id = req_data['driver_id']
        
        amount = 0.0
        try:
            keys = req_data.keys()
            if 'price_offer' in keys and req_data['price_offer'] is not None:
                amount = float(req_data['price_offer'])
            elif 'estimated_price' in keys and req_data['estimated_price'] is not None:
                amount = float(req_data['estimated_price'])
        except (ValueError, TypeError):
            amount = 0.0

        if self.model.mark_job_delivered(req_id):
            inv_model = InvoiceModel()
            inv_model.create_table()
            
            inv_id = f"INV-{str(uuid.uuid4().hex)[:6].upper()}"
            issue_date = datetime.now().strftime("%Y-%m-%d")
            
            success_inv = inv_model.insert_invoice(inv_id, req_id, client_name, amount, issue_date)

            notif_model = NotificationModel()
            if success_inv:
                notif_model.add_notification(client_name, f"🚚 Cursa {req_id} a fost livrată cu succes! Factura de ${amount:,.2f} a fost emisă.", target_url="/portal/invoices")
                notif_model.add_notification("Staff", f"⚠️ Administrativ: Cursa {req_id} a fost finalizată forțat.", target_url="/active_jobs")
                
                # --- CĂUTĂM ȘOFERUL SĂ ÎI DĂM MESAJ DE COMPLETARE ---
                if drv_id:
                    target_driver_username = self._find_driver_username(str(drv_id))
                    if target_driver_username:
                        notif_model.add_notification(target_driver_username, f"✅ Felicitări! Cursa {req_id} a fost finalizată și închisă.", target_url="/driver/portal")

                self.log_db.add_log(
                    action_type="UPDATE", target_entity="Transport Request", target_id=req_id,
                    performed_by="System/Staff", details=f"Force Closed job. Invoice {inv_id} generated."
                )
                return {"success": True, "message": f"Succes! Cursa livrată și factura emisă către {client_name}."}
            else:
                return {"success": False, "message": "Cursa s-a închis, dar crearea facturii a eșuat intern!"}
        else:
            return {"success": False, "message": "Eroare la închiderea cursei în DB."}

    def cancel_active_job(self, req_id: str, staff_username: str) -> dict:
        try:
            with sqlite3.connect("instance/database.sqlite") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT client, driver_id FROM transport_requests WHERE id = ?", (req_id,))
                req_data = cursor.fetchone()
        except Exception as e:
            return {"success": False, "message": "Database error."}

        if not req_data:
            return {"success": False, "message": "Cererea nu a fost găsită."}

        client_name = req_data['client']
        drv_id = req_data['driver_id']

        if self.model.cancel_job(req_id):
            self.log_db.add_log(
                action_type="DELETE", target_entity="Transport Request", target_id=req_id,
                performed_by=staff_username, details="Job CANCELLED. All resources freed."
            )
            
            notif_model = NotificationModel()
            notif_model.add_notification(client_name, f"❌ Ne cerem scuze! Comanda {req_id} a fost anulată de către dispecerat.", target_url="/portal")
            notif_model.add_notification("Staff", f"⚠️ Audit: {staff_username} a anulat comanda {req_id}.", target_url="/system_logs")
            notif_model.add_notification("Administrator", f"🚨 ALERTĂ: {staff_username} a anulat forțat comanda {req_id}!", target_url="/system_logs")

            # --- CĂUTĂM ȘOFERUL SĂ ÎI ZICEM CĂ E CANCELLED ---
            if drv_id:
                target_driver_username = self._find_driver_username(str(drv_id))
                if target_driver_username:
                    notif_model.add_notification(target_driver_username, f"🛑 URGENT: Dispeceratul a anulat cursa {req_id}! Oprește-te imediat.", target_url="/driver/portal")
            
            return {"success": True, "message": f"Succes! Comanda {req_id} a fost anulată complet."}
        else:
            return {"success": False, "message": "Eroare la anularea comenzii în baza de date."}