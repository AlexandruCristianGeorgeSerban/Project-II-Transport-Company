import logging
from typing import Dict, Any
from app.models.allocation_model import AllocationModel
from app.models.invoice_model import InvoiceModel
from app.models.notification_model import NotificationModel
from datetime import datetime
import uuid
import sqlite3

# Define the function OUTSIDE the class
def check_license_compatibility(driver_licenses: str, vehicle_type: str) -> bool:
    """Verifică dacă permisul șoferului îi dă dreptul să conducă mașina respectivă."""
    if not driver_licenses or not vehicle_type:
        return False
    
    # Am actualizat dicționarul ca să se potrivească cu valorile din baza de date
    rules = {
        "Van": ["B", "C", "CE"],
        "Truck": ["C", "CE"],
        "Lorrie": ["C", "CE"],
        "Semi-Trailer": ["CE"],
        "TIR": ["CE"],
        "Airplane": ["Pilot (ATPL)", "Pilot", "Pilot (Airplane)"], # Acoperă multiple variante
        "Ship": ["Maritime", "Maritime (Ship)"],                   # Aici era problema!
        "Train": ["Train Operator", "Train"]
    }

    # Curățăm lista de permise a șoferului pentru a evita erorile de spațiere
    driver_has = [lic.strip() for lic in driver_licenses.split(',')]
    allowed_licenses = rules.get(vehicle_type, [])

    for lic in driver_has:
        if lic in allowed_licenses:
            return True 
    return False

class AllocationController:
    """Processes business logic for resource allocation."""

    def __init__(self) -> None:
        """Initializes the allocation model."""
        self.model = AllocationModel()

    def load_allocation_data(self) -> Dict[str, Any]:
        """Loads all available resources and pending requests."""
        data: Dict[str, Any] = {}
        try:
            data["requests"] = self.model.get_pending_requests()
            data["vehicles"] = self.model.get_available_vehicles()
            data["drivers"] = self.model.get_available_drivers()
            return data
        except Exception as error:
            logging.error(f"Logic error loading allocation data: {error}")
            return {"requests": [], "vehicles": [], "drivers": []}

    def process_allocation(self, req_id: str, veh_id: str, drv_id: str) -> dict:
        """Handles the allocation confirmation."""
        if not req_id or not veh_id or not drv_id:
            return {"success": False, "message": "Please select a Request, a Vehicle, and a Driver!"}
            
        result = self.model.allocate_resources(req_id, veh_id, drv_id)
        
        if result is True:
            return {"success": True, "message": f"Successfully allocated Vehicle {veh_id} and Driver {drv_id} to Request {req_id}!"}
        else:
            return {"success": False, "message": "An error occurred during allocation."}
        
    def load_active_jobs(self) -> dict:
        """Încarcă datele pentru ecranul de Active Jobs."""
        return {"jobs": self.model.get_active_jobs()}

    def complete_active_job(self, req_id: str) -> dict:
        """Închide cursa, eliberează resursele, creează factura și trimite notificare."""
        try:
            with sqlite3.connect("instance/database.sqlite") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT client, estimated_price FROM transport_requests WHERE id = ?", (req_id,))
                req_data = cursor.fetchone()
        except Exception as e:
            return {"success": False, "message": "Database error."}

        if not req_data:
            return {"success": False, "message": "Cererea nu a fost găsită."}

        client_name = req_data['client']
        amount = req_data['estimated_price']

        # 1. Eliberăm resursele și închidem cursa
        if self.model.mark_job_delivered(req_id):
            
            # 2. Generăm automat Factura (Auto-Billing)
            inv_model = InvoiceModel()
            inv_id = f"INV-{str(uuid.uuid4().hex)[:6].upper()}"
            issue_date = datetime.now().strftime("%Y-%m-%d")
            inv_model.insert_invoice(inv_id, req_id, client_name, amount, issue_date)

            # 3. Notificăm Clientul că marfa a ajuns și are o factură de plată
            notif_model = NotificationModel()
            notif_model.add_notification('Customer', f"🚚 Cursa {req_id} a fost livrată cu succes! O nouă factură de ${amount} a fost emisă în portalul tău.")

            return {"success": True, "message": f"Succes! Cursa {req_id} a fost livrată. Mașina este liberă, iar factura a fost emisă automat către {client_name}."}
        else:
            return {"success": False, "message": "Eroare la închiderea cursei."}