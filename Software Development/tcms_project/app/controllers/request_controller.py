import logging
from typing import Dict, Any
from app.models.request_model import RequestModel

class RequestController:
    """Processes business logic and formats data for Transport Requests."""

    def __init__(self) -> None:
        """Initializes the model and creates the table."""
        self.model = RequestModel()
        self.model.create_table()

    def load_request_data(self) -> Dict[str, Any]:
        """Loads and structures all necessary request data."""
        req_data: Dict[str, Any] = {}
        try:
            req_data["summary"] = self.model.get_request_summary()
            req_data["requests"] = self.model.get_all_requests()
            return req_data
        except Exception as logic_error:
            logging.error(f"Error processing request data: {logic_error}")
            req_data["summary"] = {"total": 0, "pending": 0, "approved": 0}
            req_data["requests"] = []
            return req_data

    def add_new_request(self, r_id: str, client: str, c_type: str, desc: str, weight: float, volume: float, pickup: str, delivery: str, date: str, status: str) -> dict:
        """Handles logic for adding a new transport request."""
        result = self.model.insert_request(r_id, client, c_type, desc, weight, volume, pickup, delivery, date, status)
        if result is True:
            return {"success": True, "message": f"Request {r_id} created successfully!"}
        else:
            return {"success": False, "message": "Error: Request ID might already exist."}

    def modify_request(self, r_id: str, client: str, c_type: str, desc: str, weight: float, volume: float, pickup: str, delivery: str, date: str, status: str) -> dict:
        """Handles logic for updating an existing request."""
        result = self.model.update_request(r_id, client, c_type, desc, weight, volume, pickup, delivery, date, status)
        if result is True:
            return {"success": True, "message": f"Request {r_id} updated successfully!"}
        else:
            return {"success": False, "message": "Error updating request."}

    def remove_request(self, r_id: str) -> dict:
        """Handles logic for removing a request."""
        result = self.model.delete_request(r_id)
        if result is True:
            return {"success": True, "message": "Request deleted successfully!"}
        else:
            return {"success": False, "message": "Error deleting request."}
        
    def send_price_offer(self, req_id: str, price: str) -> dict:
        """Validează prețul și trimite comanda către Model pentru a actualiza cererea."""
        try:
            price_val = float(price)
            if price_val <= 0:
                return {"success": False, "message": "Prețul trebuie să fie mai mare decât 0."}
                
            # Schimbăm statusul din 'Pending' în 'Awaiting Approval'
            new_status = "Awaiting Approval"
            
            return self.model.update_request_status_and_price(req_id, new_status, price_val)
            
        except ValueError:
            return {"success": False, "message": "Format de preț invalid. Te rog introdu un număr."}
    def client_decision(self, req_id: str, decision: str) -> dict:
        """Procesează decizia clientului de a accepta sau refuza o ofertă."""
        if decision == 'accept':
            # Dacă acceptă, comanda este gata să primească șofer și mașină
            return self.model.update_request_status(req_id, "Approved")
        elif decision == 'reject':
            # Dacă refuză, o anulăm
            return self.model.update_request_status(req_id, "Canceled")
        else:
            return {"success": False, "message": "Decizie invalidă."}