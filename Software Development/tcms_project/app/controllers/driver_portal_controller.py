import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any

from app.models.driver_portal_model import DriverPortalModel
from app.models.invoice_model import InvoiceModel
from app.models.notification_model import NotificationModel
from app.controllers.log_controller import LogController # 🔴 NOU: Importăm logurile

class DriverPortalController:
    """Processes business logic for the Driver Portal."""

    def __init__(self) -> None:
        self.model = DriverPortalModel()
        self.logger = LogController() # 🔴 NOU: Inițializăm sistemul de Audit

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

    def update_job_status(self, job_id: str, new_status: str, driver_username: str = "Driver") -> dict:
        """Actualizează statusul cursei și, dacă e finalizată, emite factura automat."""
        if self.model.update_job_status(job_id, new_status):
            
            # AUDIT LOG: Înregistrăm schimbarea de status făcută de șofer
            self.logger.log_action("UPDATE", "Transport Request", job_id, driver_username, f"Driver changed route status to: {new_status}")
            
            # LOGICA BLINDATĂ DE FACTURARE
            if new_status == 'Delivered':
                try:
                    with sqlite3.connect("instance/database.sqlite") as conn:
                        conn.row_factory = sqlite3.Row
                        req_data = conn.execute("SELECT * FROM transport_requests WHERE id = ?", (job_id,)).fetchone()
                        
                    if req_data:
                        client_name = req_data['client']
                        amount = 0.0
                        
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
                            notif = NotificationModel()
                            # 🔴 NOU: Am adăugat `target_url` pentru Client și Staff
                            notif.add_notification(client_name, f"🚚 Cursa {job_id} a ajuns la destinație! Factura de ${amount:,.2f} a fost emisă.", target_url="/portal/invoices")
                            notif.add_notification('Staff', f"🏁 Șoferul a finalizat cursa {job_id}. Factura a fost generată și înregistrată automat.", target_url="/active_jobs")
                            
                            self.logger.log_action("CREATE", "Invoice", inv_id, "System", f"Invoice auto-generated for delivered Job {job_id} (${amount:,.2f})")
                        else:
                            logging.error(f"Eroare: insert_invoice a eșuat pentru job-ul {job_id}.")
                            
                except Exception as e:
                    logging.error(f"Eroare fatală la generarea facturii din portalul soferului: {e}")

            return {"success": True, "message": f"Job status successfully updated to {new_status}!"}
        return {"success": False, "message": "Could not update the status."}
        
    def set_vehicle_status(self, vehicle_id: str, status: str, driver_username: str = "Driver") -> dict:
        if self.model.update_vehicle_status(vehicle_id, status):
            
            # AUDIT LOG: Înregistrăm dacă șoferul raportează probleme la mașină (Maintenance, Broken etc)
            self.logger.log_action("UPDATE", "Vehicle", vehicle_id, driver_username, f"Driver updated vehicle status to: {status}")
            
            # 🔴 NOU: Notificare inteligentă pentru client când mașina are o problemă (Fuel, Maintenance etc)
            if status not in ['Available', 'In Transit']:
                try:
                    with sqlite3.connect("instance/database.sqlite") as conn:
                        conn.row_factory = sqlite3.Row
                        affected_jobs = conn.execute("SELECT id, client FROM transport_requests WHERE vehicle_id = ? AND status = 'In Transit'", (vehicle_id,)).fetchall()
                        
                        notif_db = NotificationModel()
                        for job in affected_jobs:
                            notif_db.add_notification(
                                job['client'], 
                                f"⚠️ Alertă Traseu: Vehiculul care îți transportă comanda ({job['id']}) a raportat o problemă: {status}.", 
                                target_url="/portal"
                            )
                except Exception as e:
                    logging.error(f"Eroare notificare client pt status vehicul: {e}")

            return {"success": True, "message": "Vehicle condition updated!"}
        return {"success": False, "message": "Error updating vehicle."}