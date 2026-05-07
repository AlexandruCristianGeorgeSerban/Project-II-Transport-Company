from typing import List, Dict, Any
from app.models.log_model import LogModel

class LogController:
    """Procesează logica pentru afișarea și adăugarea de System Logs"""
    
    def __init__(self):
        self.model = LogModel()

    def get_logs_data(self) -> List[Dict[str, Any]]:
        return self.model.get_all_logs()

    def log_action(self, action_type: str, target_entity: str, target_id: str, performed_by: str, details: str = "") -> None:
        """Poate fi apelată din alte controllere pentru a înregistra o acțiune"""
        self.model.add_log(action_type, target_entity, target_id, performed_by, details)