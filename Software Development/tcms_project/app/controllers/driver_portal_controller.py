import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any

from app.models.driver_portal_model import DriverPortalModel
from app.models.invoice_model import InvoiceModel
from app.models.notification_model import NotificationModel

class DriverPortalController:
    """Processes business logic for the Driver Portal."""

    def __init__(self) -> None:
        self.model = DriverPortalModel()

    def load_dashboard_data(self, username: str) -> Dict[str, Any]:
        """Aduce datele pentru ecranul principal (curse active și mașină)."""
        real_driver_id = self.model.get_real_driver_id(username)
        
        # Dacă Admin-ul încă nu i-a făcut cont de șofer (e doar user), dăm pagină goală
        if not real_driver_id:
            return {"my_jobs": [], "my_vehicle": None}

        jobs = self.model.get_jobs(real_driver_id, 'active')
        vehicle = self.model.get_assigned_vehicle(real_driver_id)
        
        return {"my_jobs": jobs, "my_vehicle": vehicle}
        
    def load_history_data(self, username: str) -> list:
        """Aduce istoricul curselor finalizate."""
        real_driver_id = self.model.get_real_driver_id(username)
        if not real_driver_id:
            return []
            
        return self.model.get_jobs(real_driver_id, 'history')

    def update_job_status(self, job_id: str, new_status: str) -> dict:
        """Actualizează statusul cursei și, dacă e finalizată, emite factura automat."""
        if self.model.update_job_status(job_id, new_status):
            
            # 🔴 LOGICA BLINDATĂ DE FACTURARE 
            if new_status == 'Delivered':
                try:
                    with sqlite3.connect("instance/database.sqlite") as conn:
                        conn.row_factory = sqlite3.Row
                        # Folosim SELECT * ca să nu mai crape baza de date!
                        req_data = conn.execute("SELECT * FROM transport_requests WHERE id = ?", (job_id,)).fetchone()
                        
                    if req_data:
                        client_name = req_data['client']
                        amount = 0.0
                        
                        # Căutăm cu grijă suma corectă
                        try:
                            keys = req_data.keys()
                            if 'price_offer' in keys and req_data['price_offer'] is not None:
                                amount = float(req_data['price_offer'])
                            elif 'estimated_price' in keys and req_data['estimated_price'] is not None:
                                amount = float(req_data['estimated_price'])
                        except (ValueError, TypeError):
                            amount = 0.0
                            
                        # Tăiem factura în baza de date
                        inv_model = InvoiceModel()
                        inv_model.create_table()
                        inv_id = f"INV-{str(uuid.uuid4().hex)[:6].upper()}"
                        issue_date = datetime.now().strftime("%Y-%m-%d")
                        
                        success_inv = inv_model.insert_invoice(inv_id, job_id, client_name, amount, issue_date)
                        
                        if success_inv:
                            # Trimitem Notificările ca să știe toată lumea
                            notif = NotificationModel()
                            notif.add_notification(client_name, f"🚚 Cursa {job_id} a ajuns la destinație! Factura de ${amount:,.2f} a fost emisă.")
                            notif.add_notification('Staff', f"🏁 Șoferul a finalizat cursa {job_id}. Factura a fost generată și înregistrată automat.")
                        else:
                            logging.error(f"Eroare: insert_invoice a eșuat pentru job-ul {job_id}.")
                            
                except Exception as e:
                    logging.error(f"Eroare fatală la generarea facturii din portalul soferului: {e}")
            # -------------------------------------------------------------

            return {"success": True, "message": f"Job status successfully updated to {new_status}!"}
        return {"success": False, "message": "Could not update the status."}
        
    def set_vehicle_status(self, vehicle_id: str, status: str) -> dict:
        if self.model.update_vehicle_status(vehicle_id, status):
            return {"success": True, "message": "Vehicle condition updated!"}
        return {"success": False, "message": "Error updating vehicle."}