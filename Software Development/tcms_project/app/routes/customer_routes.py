import uuid
import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from app.controllers.customer_controller import CustomerController
from app.models.support_model import SupportModel
from app.models.notification_model import NotificationModel
import sqlite3

customer_bp = Blueprint('customer', __name__)
cust_logic = CustomerController()
support_db = SupportModel()
notif_db = NotificationModel()

support_db.create_table()
notif_db.create_table() 

# Funcție pentru a activa clopoțelul pe absolut toate paginile clientului!
def get_header_data():
    try:
        username = str(session.get('username', '')).strip()
        role = str(session.get('role', 'Customer')).strip()
        # Trimitem ambele date: și numele, și rolul
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
    result = cust_logic.process_customer_response(req_id, action, username)
    
    if result.get("success"):
        flash(result.get("message"), "success")
    else:
        flash(result.get("message"), "danger")
        
    return redirect(url_for('customer.portal'))

@customer_bp.route('/portal/support', methods=['GET'])
def support() -> str:
    if 'user_id' not in session: 
        return redirect(url_for('auth.login'))
    
    username = session.get('username')
    my_tickets = support_db.get_tickets_by_client(username)
    notifications, unread_count = get_header_data()
    
    return render_template('customer/support.html', username=username, tickets=my_tickets, notifications=notifications, unread_count=unread_count)

@customer_bp.route('/portal/support/submit', methods=['POST'])
def submit_support() -> str:
    if 'user_id' not in session: 
        return redirect(url_for('auth.login'))
    
    username = session.get('username')
    message = request.form.get('support_message')
    
    if message:
        success = support_db.insert_ticket(username, message)
        if success:
            # ADMIN NOTIFICATION
            notif_db.add_notification('Administrator', f"🎧 Tichet nou deschis de clientul {username}")
            notif_db.add_notification('Staff', f"🎧 Tichet nou deschis de clientul {username}")
            flash("🎧 Message sent successfully! Our team will contact you shortly.", "success")
        else:
            flash("Error sending message. Please try again.", "danger")
    else:
        flash("Please type a message before submitting.", "warning")
        
    return redirect(url_for('customer.support'))

@customer_bp.route('/customer/support/reply/<int:ticket_id>', methods=['POST'])
def reply_support(ticket_id: int):
    if session.get('role') != 'Customer':
        return redirect(url_for('auth.login'))
    
    reply_message = request.form.get('client_reply')
    username = session.get('username')
    
    if reply_message and username:
        if support_db.add_reply(ticket_id, username, reply_message):
            # ADMIN NOTIFICATION
            notif_db.add_notification('Administrator', f"💬 Clientul {username} a răspuns la tichetul #{ticket_id}")
            notif_db.add_notification('Staff', f"💬 Clientul {username} a răspuns la tichetul #{ticket_id}")
            flash("Mesajul tău a fost trimis echipei de suport!", "success")
        else:
            flash("Eroare la trimiterea mesajului.", "danger")
            
    return redirect(url_for('customer.support'))

@customer_bp.route('/portal/invoices', methods=['GET'])
def invoices():
    if 'user_id' not in session or session.get('role') != 'Customer':
        return redirect(url_for('auth.login'))
    
    username = session.get('username')
    view_data = cust_logic.load_customer_invoices(username)
    notifications, unread_count = get_header_data()
    
    return render_template('customer/invoices.html', data=view_data, username=username, notifications=notifications, unread_count=unread_count)

@customer_bp.route('/portal/invoices/pay/<invoice_id>', methods=['POST'])
def pay_invoice(invoice_id: str):
    if 'user_id' not in session or session.get('role') != 'Customer':
        return redirect(url_for('auth.login'))
        
    resp = cust_logic.process_invoice_payment(invoice_id)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    
    return redirect(url_for('customer.invoices'))

@customer_bp.route('/api/track/<req_id>', methods=['GET'])
def get_live_location(req_id: str):
    try:
        from app.models.customer_model import DB_PATH
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT current_lat, current_lng, status FROM transport_requests WHERE id = ?", (req_id,))
            row = cursor.fetchone()
            
            if row and row['current_lat'] is not None and row['current_lng'] is not None:
                return jsonify({
                    "success": True, 
                    "lat": row['current_lat'], 
                    "lng": row['current_lng'],
                    "status": row['status']
                })
            else:
                return jsonify({"success": False, "message": "No GPS data yet."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@customer_bp.route('/customer/chat/<job_id>', methods=['GET', 'POST'])
def job_chat(job_id):
    if 'user_id' not in session or session.get('role') != 'Customer':
        flash("Please log in as a Customer.", "danger")
        return redirect(url_for('auth.login'))
        
    username = session.get('username')

    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            support_db.add_job_message(job_id, session['user_id'], 'Customer', message)
            
            # --- NOUA MAGIE DE NOTIFICARE (FĂRĂ TABELUL DRIVERS) ---
            try:
                with sqlite3.connect("instance/database.sqlite") as conn:
                    conn.row_factory = sqlite3.Row
                    req = conn.execute("SELECT driver_id, vehicle_id FROM transport_requests WHERE id = ?", (job_id,)).fetchone()
                    
                    if req:
                        d_id = str(req['driver_id'] or '').strip()
                        v_id = str(req['vehicle_id'] or '').strip()
                        
                        # Colectăm toate variantele posibile de nume pentru a fi 100% siguri că nimerim șoferul
                        tinte_posibile = set()
                        
                        if d_id and d_id.lower() != 'none':
                            tinte_posibile.add(d_id)
                            tinte_posibile.add(d_id.lower())
                            
                        if v_id and v_id.lower() != 'none':
                            tinte_posibile.add(v_id)
                            tinte_posibile.add(v_id.lower())
                            # Dacă e "SHIP-002", extragem doar "SHIP" și "ship"
                            prefix = v_id.split('-')[0]
                            tinte_posibile.add(prefix)
                            tinte_posibile.add(prefix.lower())
                        
                        # Trimitem notificarea către TOATE variantele posibile simultan!
                        # Astfel, indiferent cum s-a logat șoferul (ship, SHIP, Ship), o va primi garantat.
                        for tinta in tinte_posibile:
                            notif_db.add_notification(tinta, f"💬 Clientul {username} ți-a scris la cursa {job_id}")
                            
            except Exception as e:
                logging.error(f"Eroare notificare chat client: {e}")
            # ---------------------------------------------
                
        return redirect(url_for('customer.job_chat', job_id=job_id))

    messages = support_db.get_job_messages(job_id)
    notifications, unread_count = get_header_data()
    return render_template('customer/job_chat.html', job_id=job_id, messages=messages, username=username, notifications=notifications, unread_count=unread_count)