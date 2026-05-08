import logging
from typing import Dict, Any
from app.models.allocation_model import AllocationModel
from app.models.invoice_model import InvoiceModel
from app.models.notification_model import NotificationModel
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
    """Processes business logic for resource allocation."""

    def __init__(self) -> None:
        self.model = AllocationModel()

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
            # Validări Capacitate și Licențe
            constraints = self.model.get_allocation_constraints(req_id, veh_id, drv_id)
            if constraints and "weight" in constraints and "capacity" in constraints:
                if constraints["weight"] > constraints["capacity"]:
                    return {"success": False, "message": f"❌ Eroare: Capacitatea mașinii ({constraints['capacity']}) e prea mică pt greutatea mărfii ({constraints['weight']})!"}
            if constraints and "driver_licenses" in constraints and "vehicle_type" in constraints:
                if not check_license_compatibility(constraints["driver_licenses"], constraints["vehicle_type"]):
                    return {"success": False, "message": f"❌ Eroare Permis: Șoferul nu are licența necesară!"}
        except Exception:
            pass

        result = self.model.allocate_resources(req_id, veh_id, drv_id, staff_username)
        if result is True:
            return {"success": True, "message": f"Successfully allocated Vehicle {veh_id} and Driver {drv_id} to Request {req_id}!"}
        else:
            return {"success": False, "message": "An error occurred during allocation."}
        
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
        """Închide cursa (Override administrativ), eliberează resursele, creează factura inteligent și trimite notificare."""
        try:
            with sqlite3.connect("instance/database.sqlite") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # 🔴 REPARAȚIE CRITICĂ: Extragem tot rândul, inclusiv preturile negociate!
                cursor.execute("SELECT * FROM transport_requests WHERE id = ?", (req_id,))
                req_data = cursor.fetchone()
        except Exception as e:
            return {"success": False, "message": "Database error."}

        if not req_data:
            return {"success": False, "message": "Cererea nu a fost găsită."}

        client_name = req_data['client']
        
        # 🔴 LOGICĂ NOUĂ PREȚ: Ia oferta dacă există, dacă nu ia estimarea, dacă nu pune 0.0
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
            
            # Acum avem un număr real la "amount" mereu, deci factura SE VA CREA!
            success_inv = inv_model.insert_invoice(inv_id, req_id, client_name, amount, issue_date)

            notif_model = NotificationModel()
            if success_inv:
                notif_model.add_notification(client_name, f"🚚 Cursa {req_id} a fost livrată cu succes! Factura de ${amount:,.2f} a fost emisă.")
                notif_model.add_notification("Staff", f"⚠️ Administrativ: Cursa {req_id} a fost finalizată forțat și factura generată.")
                return {"success": True, "message": f"Succes! Cursa livrată și factura emisă către {client_name}."}
            else:
                return {"success": False, "message": "Atenție: Cursa s-a închis, dar crearea facturii a eșuat intern!"}
        else:
            return {"success": False, "message": "Eroare la închiderea cursei în DB."}