import logging
import sqlite3
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.controllers.request_controller import RequestController
from app.models.user_model import UserModel

request_bp = Blueprint('request_routes', __name__)
req_logic = RequestController()

@request_bp.route('/requests', methods=['GET'])
def request_management() -> str:
    if 'user_id' not in session:
        flash("Please log in.", "danger")
        return redirect(url_for('auth.login'))
    
    view_data = req_logic.load_request_data()
    role = session.get('role', 'Staff')
    
    all_users = UserModel().get_all_users()
    customers = [u for u in all_users if u['role'] == 'Customer']
    
    return render_template('admin/requests.html', data=view_data, role=role, customers=customers)

@request_bp.route('/requests/add', methods=['POST'])
def add_request() -> str:
    r_id = request.form.get('request_id')
    client = request.form.get('client_name')
    c_type = request.form.get('cargo_type')
    desc = request.form.get('description')
    weight = float(request.form.get('weight', 0.0))
    volume = float(request.form.get('volume', 0.0))
    pickup = request.form.get('pickup')
    delivery = request.form.get('delivery')
    date = request.form.get('preferred_date')
    status = request.form.get('status')
    
    resp = req_logic.add_new_request(r_id, client, c_type, desc, weight, volume, pickup, delivery, date, status)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('request_routes.request_management'))

@request_bp.route('/requests/edit', methods=['POST'])
def edit_request() -> str:
    r_id = request.form.get('edit_request_id')
    client = request.form.get('edit_client_name')
    c_type = request.form.get('edit_cargo_type')
    desc = request.form.get('edit_description')
    weight = float(request.form.get('edit_weight', 0.0))
    volume = float(request.form.get('edit_volume', 0.0))
    pickup = request.form.get('edit_pickup')
    delivery = request.form.get('edit_delivery')
    date = request.form.get('edit_preferred_date')
    status = request.form.get('edit_status')
    staff_username = session.get('username', 'Unknown')
    
    resp = req_logic.modify_request(r_id, client, c_type, desc, weight, volume, pickup, delivery, date, status, staff_username)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('request_routes.request_management'))

@request_bp.route('/requests/delete/<req_id>', methods=['POST'])
def delete_request(req_id: str) -> str:
    resp = req_logic.remove_request(req_id)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('request_routes.request_management'))

@request_bp.route('/send_offer/<req_id>', methods=['POST'])
def send_offer(req_id: str) -> str:
    if session.get('role') not in ['Administrator', 'Staff']:
        return redirect(url_for('dashboard.main_dashboard'))
    price = request.form.get('price_offer')
    resp = req_logic.send_price_offer(req_id, price)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('dashboard.main_dashboard'))

@request_bp.route('/requests/negotiate/<req_id>', methods=['POST'])
def staff_negotiate(req_id: str):
    role = session.get('role')
    if role not in ['Administrator', 'Staff']:
        return redirect(url_for('dashboard.main_dashboard'))
    
    price_str = request.form.get('new_price')
    price = float(price_str) if price_str and price_str.strip() else 0.0
    
    msg = request.form.get('message', '')
    username = session.get('username', 'Unknown')
    
    resp = req_logic.handle_negotiation_offer(req_id, username, msg, price, role)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    
    return redirect(request.referrer or url_for('dashboard.main_dashboard'))

# --- ROUTE OPTIMIZATION (HARTA FLOTEI) ---
@request_bp.route('/staff/optimization')
def route_optimization():
    """Afișează harta de optimizare a rutelor și locația vehiculelor în tranzit."""
    if 'user_id' not in session or session.get('role') not in ['Administrator', 'Staff']:
        flash("Acces interzis.", "danger")
        return redirect(url_for('auth.login'))
    
    role = session.get('role')
    return render_template('staff/optimization.html', role=role)

# --- INVOICE MANAGEMENT PENTRU STAFF ---
@request_bp.route('/staff/invoices')
def staff_invoices():
    """Afișează toate facturile emise de sistem către clienți."""
    if 'user_id' not in session or session.get('role') not in ['Administrator', 'Staff']:
        flash("Acces interzis.", "danger")
        return redirect(url_for('auth.login'))
        
    role = session.get('role')
    
    from app.models.invoice_model import DB_PATH
    
    invoices = []
    summary = {"total_amount": 0, "paid_amount": 0, "pending_amount": 0}
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices ORDER BY issue_date DESC")
            rows = cursor.fetchall()
            
            for row in rows:
                inv = dict(row)
                invoices.append(inv)
                
                summary["total_amount"] += inv["amount"]
                if inv["status"] == "Paid":
                    summary["paid_amount"] += inv["amount"]
                else:
                    summary["pending_amount"] += inv["amount"]
                    
    except Exception as e:
        logging.error(f"Eroare la incarcarea facturilor staff: {e}")
        
    return render_template('staff/invoices_management.html', invoices=invoices, summary=summary, role=role)

@request_bp.route('/staff/invoices/remind/<invoice_id>', methods=['POST'])
def send_invoice_reminder(invoice_id: str):
    """Trimite o notificare (Reminder) clientului pentru a-și plăti factura."""
    if 'user_id' not in session or session.get('role') not in ['Administrator', 'Staff']:
        return redirect(url_for('auth.login'))
        
    client_name = request.form.get('client_name', 'Client')
    amount = request.form.get('amount', '0')
    
    from app.models.notification_model import NotificationModel
    notif_db = NotificationModel()
    notif_db.add_notification(client_name, f"⚠️ Memento Plată: Factura {invoice_id} în valoare de ${amount} este scadentă. Te rugăm să achiți contravaloarea.")
    
    flash(f"Un memento de plată a fost trimis către {client_name}.", "success")
    return redirect(url_for('request_routes.staff_invoices'))