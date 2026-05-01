from app.models.driver_portal_model import DriverPortalModel

class DriverPortalController:
    """Contine logica de business pentru actiunile soferului."""
    
    def __init__(self):
        self.model = DriverPortalModel()

    def get_driver_jobs(self, username: str) -> list:
        return self.model.get_jobs_by_driver(username)

    def update_status(self, req_id: str, new_status: str, username: str) -> dict:
        valid_statuses = ['In Transit', 'Delivered']
        if new_status not in valid_statuses:
            return {"success": False, "message": "Status invalid!"}

        success = self.model.update_job_status(req_id, new_status, username)
        
        if success:
            return {"success": True, "message": f"Status actualizat cu succes la: {new_status} 🚚"}
        else:
            return {"success": False, "message": "Eroare: Cursa nu a fost gasita sau nu iti apartine."}