import logging
from typing import Dict, Any
from app.models.request_model import RequestModel
from app.controllers.log_controller import LogController

class RequestController:
    def __init__(self) -> None:
        self.model = RequestModel()
        self.model.create_table()
        self.logger = LogController()

    def load_request_data(self) -> Dict[str, Any]:
        req_data: Dict[str, Any] = {}
        try:
            req_data["summary"] = self.model.get_request_summary()
            reqs = self.model.get_all_requests()
            for r in reqs:
                r["messages"] = self.model.get_negotiation_messages(r["id"])
            req_data["requests"] = reqs
            return req_data
        except Exception as logic_error:
            logging.error(f"Error processing request data: {logic_error}")
            return {"summary": {"total": 0, "pending": 0, "approved": 0}, "requests": []}

    def add_new_request(self, r_id: str, client: str, c_type: str, desc: str, weight: float, volume: float, pickup: str, delivery: str, date: str, status: str, modified_by: str = "System") -> dict:
        result = self.model.insert_request(r_id, client, c_type, desc, weight, volume, pickup, delivery, date, status)
        if result is True:
            self.logger.log_action("CREATE", "Request", r_id, modified_by, f"Created new request for {client}. Cargo: {c_type}")
            return {"success": True, "message": f"Request {r_id} created successfully!"}
        else:
            return {"success": False, "message": "Error: Request ID might already exist."}

    def modify_request(self, r_id: str, client: str, c_type: str, desc: str, weight: float, volume: float, pickup: str, delivery: str, date: str, status: str, staff_username: str = 'Unknown') -> dict:
        result = self.model.update_request(r_id, client, c_type, desc, weight, volume, pickup, delivery, date, status, staff_username)
        if result is True:
            log_details = f"Client: {client} | Cargo: {c_type} | Status: {status} | Route: {pickup} -> {delivery}"
            self.logger.log_action("UPDATE", "Request", r_id, staff_username, log_details)
            return {"success": True, "message": f"Request {r_id} updated successfully!"}
        else:
            return {"success": False, "message": "Error updating request."}

    def remove_request(self, r_id: str, modified_by: str = "System") -> dict:
        result = self.model.delete_request(r_id)
        if result is True:
            self.logger.log_action("DELETE", "Request", r_id, modified_by, "Deleted transport request")
            return {"success": True, "message": "Request deleted successfully!"}
        else:
            return {"success": False, "message": "Error deleting request."}
                    
    def send_price_offer(self, req_id: str, price: str) -> dict:
        try:
            price_val = float(price)
            if price_val <= 0:
                return {"success": False, "message": "Prețul trebuie să fie mai mare decât 0."}
            new_status = "Pending"  
            return self.model.update_request_status_and_price(req_id, new_status, price_val)
        except ValueError:
            return {"success": False, "message": "Format de preț invalid."}
            
    def client_decision(self, req_id: str, decision: str) -> dict:
        if decision == 'accept':
            return self.model.update_request_status(req_id, "Approved")
        elif decision == 'reject':
            return self.model.update_request_status(req_id, "Rejected")
        else:
            return {"success": False, "message": "Decizie invalidă."}

    
    def handle_negotiation_offer(self, req_id: str, staff_username: str, message: str, new_price: float, role: str = "Staff") -> dict:
        req = self.model.get_request_by_id(req_id)
        if not req: return {"success": False, "message": "Request nu a fost găsit."}
        
        current_price = req.get('price_offer')
        if current_price is None:
            current_price = req.get('estimated_price', 0)
        
        current_price = float(current_price or 0)
        
        if new_price > 0:
            if new_price >= current_price:
                return {"success": False, "message": f"Eroare Matematică: Noua ofertă (${new_price}) trebuie să fie STRICT MAI MICĂ decât oferta refuzată (${current_price}). Fii rațional!"}
            
            final_message = f"{message} [💲 Ofertă Nouă: ${new_price}]"
            
            self.model.add_negotiation_message(req_id, f"{role} ({staff_username})", final_message)
            self.model.update_request_status_and_price(req_id, "Pending", new_price)
            return {"success": True, "message": "Ofertă nouă trimisă către client cu succes!"}
        
        else:
            self.model.add_negotiation_message(req_id, f"{role} ({staff_username})", message)
            return {"success": True, "message": "Mesajul a fost trimis către client pe chat!"}