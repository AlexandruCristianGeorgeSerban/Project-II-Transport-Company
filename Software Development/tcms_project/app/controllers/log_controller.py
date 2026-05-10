from typing import List, Dict, Any
from app.models.log_model import LogModel
from app.models.notification_model import NotificationModel # 🔴 NOU: Importam notificările

class LogController:
    """Procesează logica pentru afișarea și adăugarea de System Logs"""
    
    def __init__(self):
        self.model = LogModel()
        self.notif_db = NotificationModel() # 🔴 NOU: Instantiem baza de date de notificari

    def get_logs_data(self) -> List[Dict[str, Any]]:
        return self.model.get_all_logs()

    def log_action(self, action_type: str, target_entity: str, target_id: str, performed_by: str, details: str = "") -> None:
        """Poate fi apelată din alte controllere pentru a înregistra o acțiune"""
        
        # 1. Adăugăm în baza de date de System Logs
        success = self.model.add_log(action_type, target_entity, target_id, performed_by, details)
        
        # 🔴 2. Dacă a mers și este o acțiune "Critica" (Delete, Warning, Cancel etc.), notificăm Adminul!
        if success and action_type in ["DELETE", "WARNING"]:
            alert_msg = f"🛡️ Audit Alert: {performed_by} performed a {action_type} on {target_entity} ({target_id})."
            # Îl trimitem direct pe pagina de loguri!
            self.notif_db.add_notification("Administrator", alert_msg, target_url="/system_logs")