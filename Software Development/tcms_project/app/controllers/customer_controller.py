import logging
from typing import Dict, Any
from app.models.customer_model import CustomerModel
from app.models.request_model import RequestModel
from app.models.invoice_model import InvoiceModel
from app.models.notification_model import NotificationModel  

class CustomerController:
    """Processes business logic for Customer Dashboard and Negotiations."""

    def __init__(self) -> None:
        self.model = CustomerModel()
        self.req_model = RequestModel()
        self.invoice_model = InvoiceModel()
        self.invoice_model.create_table()

    def get_portal_data(self, username: str) -> Dict[str, Any]:
        """Loads and calculates dashboard stats for the customer."""
        data: Dict[str, Any] = {}
        try:
            requests = self.model.get_customer_requests(username)
            data['requests'] = requests
            data['total'] = len(requests)
            data['pending'] = sum(1 for r in requests if r['status'] in ['Pending', 'Negotiation'])
            data['active'] = sum(1 for r in requests if r['status'] in ['Accepted', 'In Transit'])
            return data
        except Exception as error:
            logging.error(f"Error processing portal data: {error}")
            return {'requests': [], 'total': 0, 'pending': 0, 'active': 0}

    def process_customer_response(self, request_id: str, response_type: str, username: str) -> dict:
        """Handles the Accept / Reject / Negotiate workflow and notifies Staff (REQ-59, 60, 61)."""
        if response_type == 'accept':
            new_status = 'Accepted'  # Status care aprobă cursa
            msg = "Offer accepted! Awaiting driver allocation."
            notif_msg = f"✅ Clientul {username} a ACCEPTAT oferta pentru cererea {request_id}. Marfa este gata de alocare!"
        elif response_type == 'reject':
            new_status = 'Rejected'  
            msg = "Offer rejected. The request is closed."
            notif_msg = f"❌ Clientul {username} a RESPINS oferta pentru cererea {request_id}."
        elif response_type == 'negotiate':
            new_status = 'Negotiation'
            msg = "Negotiation sent. Awaiting admin review."
            notif_msg = f"⚠️ Clientul {username} a cerut NEGOCIERE pentru cererea {request_id}."
        else:
            return {"success": False, "message": "Invalid response type."}

        
        success = self.model.update_request_status(request_id, new_status, username)
        
        if success is True:
            NotificationModel().add_notification("Staff", notif_msg)
            return {"success": True, "message": msg}
        else:
            return {"success": False, "message": "Failed to update status. Please try again."}
        
    def load_customer_invoices(self, username: str) -> Dict[str, Any]:
        """Loads all invoices for the logged-in customer."""
        data: Dict[str, Any] = {}
        try:
            data["invoices"] = self.invoice_model.get_client_invoices(username)
            return data
        except Exception as error:
            logging.error(f"Error loading invoices: {error}")
            data["invoices"] = []
            return data

    def process_invoice_payment(self, invoice_id: str) -> dict:
        """Simulates the payment of an invoice."""
        result = self.invoice_model.mark_as_paid(invoice_id)
        if result is True:
            return {"success": True, "message": f"Payment for invoice {invoice_id} processed successfully!"}
        else:
            return {"success": False, "message": "Failed to process payment."}