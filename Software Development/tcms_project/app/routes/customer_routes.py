import uuid
import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.controllers.customer_controller import CustomerController
from app.models.support_model import SupportModel

customer_bp = Blueprint('customer', __name__)
cust_logic = CustomerController()
support_db = SupportModel()

support_db.create_table()

@customer_bp.route('/portal', methods=['GET'])
def portal() -> str:
    """Renders the Customer Portal."""
    if 'user_id' not in session or session.get('role') != 'Customer':
        return redirect(url_for('auth.login'))
        
    username = session.get('username', 'Customer')
    portal_data = cust_logic.get_portal_data(username)
    
    return render_template('customer/portal.html', data=portal_data, username=username)

@customer_bp.route('/portal/submit', methods=['POST'])
def submit_request() -> str:
    """Handles the creation of a new transport request with unit conversion."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    username = session.get('username', 'Customer')
    r_id = "REQ-" + str(uuid.uuid4().hex)[:6].upper()
    
    c_type = request.form.get('cargo_type')
    v_type = request.form.get('vehicle_type')
    desc = request.form.get('description')
    
    raw_weight = float(request.form.get('weight', 0.0))
    weight_unit = request.form.get('weight_unit', 'kg')
    final_weight = raw_weight * 1000 if weight_unit == 'tons' else raw_weight
    
    volume = float(request.form.get('volume', 0.0))
    pickup = request.form.get('pickup')
    delivery = request.form.get('delivery')
    date = request.form.get('preferred_date')
    
    base_price = 50.0
    weight_cost = final_weight * 0.15
    estimated_price = round(base_price + weight_cost, 2)
    
    status = "Pending"
    
    success = cust_logic.model.insert_customer_request(
        r_id, username, c_type, desc, final_weight, volume, pickup, delivery, date, status, v_type, estimated_price
    )
    
    if success:
        flash(f"🎉 Request submitted! Estimated initial price: ${estimated_price}", "success")
    else:
        flash("Error submitting request. Please try again.", "danger")
        
    return redirect(url_for('customer.portal'))

@customer_bp.route('/portal/response/<req_id>/<action>', methods=['POST'])
def handle_response(req_id: str, action: str) -> str:
    """Handles Accept/Reject/Negotiate."""
    username = session.get('username')
    result = cust_logic.process_customer_response(req_id, action, username)
    
    if result.get("success"):
        flash(result.get("message"), "success")
    else:
        flash(result.get("message"), "danger")
        
    return redirect(url_for('customer.portal'))

@customer_bp.route('/portal/support', methods=['GET'])
def support() -> str:
    """Afișează pagina de suport cu istoricul mesajelor."""
    if 'user_id' not in session: 
        return redirect(url_for('auth.login'))
    
    username = session.get('username')
    # Aducem mesajele clientului din baza de date
    my_tickets = support_db.get_tickets_by_client(username)
    
    return render_template('customer/support.html', username=username, tickets=my_tickets)

@customer_bp.route('/portal/support/submit', methods=['POST'])
def submit_support() -> str:
    """Handles the support form submission."""
    if 'user_id' not in session: 
        return redirect(url_for('auth.login'))
    
    username = session.get('username')
    message = request.form.get('support_message')
    
    if message:
        success = support_db.insert_ticket(username, message)
        if success:
            flash("🎧 Message sent successfully! Our team will contact you shortly.", "success")
        else:
            flash("Error sending message. Please try again.", "danger")
    else:
        flash("Please type a message before submitting.", "warning")
        
    return redirect(url_for('customer.support'))

@customer_bp.route('/portal/invoices', methods=['GET'])
def invoices():
    """Renders the Customer Invoices page."""
    if 'user_id' not in session or session.get('role') != 'Customer':
        return redirect(url_for('auth.login'))
    
    username = session.get('username')
    view_data = cust_logic.load_customer_invoices(username)
    
    return render_template('customer/invoices.html', data=view_data)

@customer_bp.route('/portal/invoices/pay/<invoice_id>', methods=['POST'])
def pay_invoice(invoice_id: str):
    """Processes a payment for an invoice."""
    if 'user_id' not in session or session.get('role') != 'Customer':
        return redirect(url_for('auth.login'))
        
    resp = cust_logic.process_invoice_payment(invoice_id)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    
    return redirect(url_for('customer.invoices'))