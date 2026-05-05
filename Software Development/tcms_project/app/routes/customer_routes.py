import uuid
import logging
import sqlite3
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from app.controllers.customer_controller import CustomerController
from app.models.support_model import SupportModel
from app.models.notification_model import NotificationModel

customer_bp = Blueprint('customer', __name__)
cust_logic = CustomerController()
support_db = SupportModel()
notif_db = NotificationModel()

support_db.create_table()
notif_db.create_table() 

def get_header_data():
    try:
        username = str(session.get('username', '')).strip()
        role = str(session.get('role', 'Customer')).strip()
        all_notifs = notif_db.get_unread_notifications(username, role)
        return all_notifs, len(all_notifs)
    except Exception as e:
        logging.error(f"Error fetching notifications for customer: {e}")
        return [], 0

@customer_bp.route('/portal', methods=['GET'])
def portal() -> str:
    if 'user_id' not in session or session.get('role') != 'Customer':
        return redirect(url_for('auth.login'))
        
    username = session.get('username', 'Customer')
    portal_data = cust_logic.get_portal_data(username)
    
    
    from app.models.request_model import RequestModel
    req_model = RequestModel()
    for r in portal_data['requests']:
        r['messages'] = req_model.get_negotiation_messages(r['id'])
        
    notifications, unread_count = get_header_data()
    
    return render_template('customer/portal.html', data=portal_data, username=username, notifications=notifications, unread_count=unread_count)

@customer_bp.route('/portal/submit', methods=['POST'])
def submit_request() -> str:
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    username = session.get('username', 'Customer')
    r_id = "REQ-" + str(uuid.uuid4().hex)[:6].upper()
    c_type = request.form.get('cargo_type') or "Standard Cargo"
    v_type = request.form.get('vehicle_type') or "Any Vehicle"
    desc = request.form.get('description') or "No description provided"
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
        notif_db.add_notification('Staff', f"Nouă cerere de transport ({r_id}) primită de la {username}!")
        flash(f"🎉 Request submitted! Estimated initial price: ${estimated_price}", "success")
    else:
        flash("Error submitting request. Please try again.", "danger")
    return redirect(url_for('customer.portal'))

@customer_bp.route('/portal/response/<req_id>/<action>', methods=['POST'])
def handle_response(req_id: str, action: str) -> str:
    username = session.get('username')
    
    
    if action == 'negotiate':
        msg = request.form.get('negotiate_message', 'Doresc o renegociere a prețului.')
        
        from app.models.request_model import RequestModel
        req_model = RequestModel()
        req_model.update_request_status(req_id, "Negotiation")
        req_model.add_negotiation_message(req_id, f"Client ({username})", msg)
        
        notif_db.add_notification('Staff', f"💬 Clientul {username} vrea să negocieze cursa {req_id}!")
        flash("Mesajul tău de negociere a fost trimis cu succes către echipa de logistică!", "success")
    else:
        # AICI E PT ACCEPT / REJECT
        result = cust_logic.process_customer_response(req_id, action, username)
        if result.get("success"):
            flash(result.get("message"), "success")
        else:
            flash(result.get("message"), "danger")
            
    return redirect(url_for('customer.portal'))

@customer_bp.route('/portal/support', methods=['GET'])
def support() -> str:
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    username = session.get('username')
    my_tickets = support_db.get_tickets_by_client(username)
    notifications, unread_count = get_header_data()
    return render_template('customer/support.html', username=username, tickets=my_tickets, notifications=notifications, unread_count=unread_count)

@customer_bp.route('/portal/support/submit', methods=['POST'])
def submit_support() -> str:
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    username = session.get('username')
    message = request.form.get('support_message')
    if message:
        if support_db.insert_ticket(username, message):
            notif_db.add_notification('Administrator', f"🎧 Tichet nou de la {username}")
            notif_db.add_notification('Staff', f"🎧 Tichet nou de la {username}")
            flash("Message sent successfully!", "success")
        else:
            flash("Error sending message.", "danger")
    return redirect(url_for('customer.support'))

@customer_bp.route('/customer/support/reply/<int:ticket_id>', methods=['POST'])
def reply_support(ticket_id: int):
    if session.get('role') != 'Customer': return redirect(url_for('auth.login'))
    reply_message = request.form.get('client_reply')
    username = session.get('username')
    if reply_message and username:
        if support_db.add_reply(ticket_id, username, reply_message):
            notif_db.add_notification('Administrator', f"💬 Clientul {username} a răspuns la tichetul #{ticket_id}")
            notif_db.add_notification('Staff', f"💬 Clientul {username} a răspuns la tichetul #{ticket_id}")
            flash("Mesajul tău a fost trimis!", "success")
    return redirect(url_for('customer.support'))

@customer_bp.route('/portal/invoices', methods=['GET'])
def invoices():
    if 'user_id' not in session or session.get('role') != 'Customer': return redirect(url_for('auth.login'))
    username = session.get('username')
    view_data = cust_logic.load_customer_invoices(username)
    notifications, unread_count = get_header_data()
    return render_template('customer/invoices.html', data=view_data, username=username, notifications=notifications, unread_count=unread_count)

@customer_bp.route('/portal/invoices/pay/<invoice_id>', methods=['POST'])
def pay_invoice(invoice_id: str):
    if 'user_id' not in session or session.get('role') != 'Customer': return redirect(url_for('auth.login'))
    resp = cust_logic.process_invoice_payment(invoice_id)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('customer.invoices'))

@customer_bp.route('/api/track/<req_id>', methods=['GET'])
def get_live_location(req_id: str):
    try:
        from app.models.customer_model import DB_PATH
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.cursor().execute("SELECT current_lat, current_lng, status FROM transport_requests WHERE id = ?", (req_id,)).fetchone()
            if row and row['current_lat'] and row['current_lng']:
                return jsonify({"success": True, "lat": row['current_lat'], "lng": row['current_lng'], "status": row['status']})
            return jsonify({"success": False, "message": "No GPS data yet."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@customer_bp.route('/customer/chat/<job_id>', methods=['GET', 'POST'])
def job_chat(job_id):
    # MAGIA AICI: Indiferent cum vine link-ul, forțăm ID-ul să aibă LITERE MARI!
    job_id = str(job_id).upper()
    
    if 'user_id' not in session or session.get('role') != 'Customer':
        return redirect(url_for('auth.login'))
    username = session.get('username')

    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            support_db.add_job_message(job_id, session['user_id'], 'Customer', message)
            try:
                with sqlite3.connect("instance/database.sqlite") as conn:
                    conn.row_factory = sqlite3.Row
                    req = conn.execute("SELECT driver_id, vehicle_id FROM transport_requests WHERE id = ?", (job_id,)).fetchone()
                    if req:
                        d_id, v_id = str(req['driver_id'] or '').strip(), str(req['vehicle_id'] or '').strip()
                        tinte = set()
                        if d_id and d_id.lower() != 'none': tinte.update([d_id, d_id.lower()])
                        if v_id and v_id.lower() != 'none': tinte.update([v_id, v_id.lower(), v_id.split('-')[0], v_id.split('-')[0].lower()])
                        for tinta in tinte: notif_db.add_notification(tinta, f"💬 Clientul {username} ți-a scris la cursa {job_id}")
            except Exception as e:
                logging.error(f"Eroare notificare chat client: {e}")
        return redirect(url_for('customer.job_chat', job_id=job_id))

    messages = support_db.get_job_messages(job_id)
    notifications, unread_count = get_header_data()
    return render_template('customer/job_chat.html', job_id=job_id, messages=messages, username=username, notifications=notifications, unread_count=unread_count)