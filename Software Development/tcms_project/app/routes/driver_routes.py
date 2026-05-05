import sqlite3
import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from app.controllers.driver_portal_controller import DriverPortalController
from app.controllers.driver_controller import DriverController
from app.models.support_model import SupportModel 
from app.models.notification_model import NotificationModel

driver_bp = Blueprint('driver', __name__)
driver_logic = DriverController()
driver_portal_logic = DriverPortalController()
support_db = SupportModel() 
notif_db = NotificationModel()
notif_db.create_table()

DB_PATH = "instance/database.sqlite"



def get_header_data():
    """Aduce notificările și numărul lor pentru clopoțelul din meniul de sus."""
    username = str(session.get('username', '')).strip()
    role = str(session.get('role', 'Driver')).strip()
    try:
        # Acum cerem notificări trimise direct către 'ship' SAU către grupul 'Driver'
        notifications = notif_db.get_unread_notifications(username, role)
        unread_count = len(notifications)
    except Exception as e:
        logging.error(f"Error fetching notifications: {e}")
        notifications = []
        unread_count = 0
    return notifications, unread_count

def get_driver_jobs(user_id, username, status_type='active'):
    jobs = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_ids = {str(user_id), str(username)}
            
            cursor.execute("PRAGMA table_info(drivers)")
            d_cols = [c[1] for c in cursor.fetchall()]
            
            if 'username' in d_cols:
                cursor.execute("SELECT id, name FROM drivers WHERE username = ?", (username,))
                for r in cursor.fetchall():
                    search_ids.add(str(r['id']))
                    search_ids.add(str(r['name']))
                    
            if 'user_id' in d_cols:
                cursor.execute("SELECT id, name FROM drivers WHERE user_id = ?", (user_id,))
                for r in cursor.fetchall():
                    search_ids.add(str(r['id']))
                    search_ids.add(str(r['name']))
                
            cursor.execute("SELECT name FROM drivers WHERE id = ?", (user_id,))
            for r in cursor.fetchall():
                search_ids.add(str(r['name']))

            valid_ids = list(search_ids)
            placeholders = ','.join(['?'] * len(valid_ids))
            status_filter = "IN ('Accepted', 'In Transit')" if status_type == 'active' else "== 'Delivered'"
            
            query = f"SELECT * FROM transport_requests WHERE CAST(driver_id AS TEXT) IN ({placeholders}) AND status {status_filter}"
            cursor.execute(query, valid_ids)
            jobs = [dict(row) for row in cursor.fetchall()]

            if not jobs and status_type == 'active':
                cursor.execute("SELECT * FROM transport_requests WHERE status IN ('Accepted', 'In Transit')")
                all_active = [dict(row) for row in cursor.fetchall()]
                
                u_name_low = str(username).lower()
                for j in all_active:
                    d_id_str = str(j.get('driver_id', '')).lower()
                    v_id_str = str(j.get('vehicle_id', '')).lower()
                    
                    if u_name_low in v_id_str or u_name_low in d_id_str:
                        if j not in jobs:
                            jobs.append(j)

    except Exception as e:
        logging.error(f"Database error in get_driver_jobs: {e}")
    return jobs



@driver_bp.route('/driver_portal')
@driver_bp.route('/active_jobs') 
def portal():
    if 'user_id' not in session or session.get('role') != 'Driver':
        flash("Access denied. Drivers only.", "danger")
        return redirect(url_for('auth.login'))
        
    user_id = session.get('user_id')
    username = session.get('username')
    
    notifications, unread_count = get_header_data()
    
    data = {'my_jobs': [], 'my_vehicle': None}
    active_jobs = get_driver_jobs(user_id, username, 'active')
    data['my_jobs'] = active_jobs
    
    if active_jobs and len(active_jobs) > 0:
        veh_id = active_jobs[0].get('vehicle_id')
        if veh_id:
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM vehicles WHERE id = ? OR plate_number = ?", (str(veh_id), str(veh_id)))
                    veh = cursor.fetchone()
                    if veh:
                        data['my_vehicle'] = dict(veh)
            except Exception as e:
                logging.error(f"Eroare extragere vehicul: {e}")
    
    return render_template('driver/portal.html', 
                           data=data, 
                           notifications=notifications, 
                           unread_count=unread_count)

@driver_bp.route('/driver/history')
def history():
    if 'user_id' not in session or session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    username = session.get('username')
    
    notifications, unread_count = get_header_data()
    jobs = get_driver_jobs(user_id, username, 'history')

    return render_template('driver/history.html', 
                           jobs=jobs, 
                           notifications=notifications, 
                           unread_count=unread_count)

@driver_bp.route('/driver_portal/update_status/<job_id>/<new_status>', methods=['POST'])
def update_job_status(job_id, new_status):
    if 'user_id' not in session or session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))

    response = driver_portal_logic.update_job_status(job_id, new_status)
    flash(response['message'], "success" if response['success'] else "danger")
    return redirect(url_for('driver.portal'))

@driver_bp.route('/driver_portal/update_vehicle_status', methods=['POST'])
def update_vehicle_status():
    if 'user_id' not in session or session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))

    vehicle_id = request.form.get('vehicle_id')
    new_status = request.form.get('status')
    driver_name = session.get('username')

    if not vehicle_id:
        flash("Eroare: Vehicul negăsit.", "danger")
        return redirect(url_for('driver.portal'))
    
    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute("UPDATE vehicles SET status = ? WHERE id = ?", (new_status, vehicle_id))
            connection.commit()
            
        active_jobs = get_driver_jobs(session.get('user_id'), driver_name, 'active')
            
        alert_icon = "🟢" if new_status == 'Active' else "⚠️"
        
        admin_msg = f"{alert_icon} Șoferul {driver_name} a schimbat statusul vehiculului în: {new_status}."
        notif_db.add_notification('Administrator', admin_msg)
        notif_db.add_notification('Staff', admin_msg)
        
        for job in active_jobs:
            client_username = str(job['client']).strip() 
            req_id = job['id']
            client_msg = f"{alert_icon} Update pentru cursa {req_id}: Vehiculul tău a raportat statusul '{new_status}'."
            notif_db.add_notification(client_username, client_msg)
                
        flash(f"Statusul mașinii a fost actualizat la: {new_status}. Notificările au fost trimise!", "success")
    except Exception as e:
        logging.error(f"Eroare notificare status vehicul: {e}")
        flash(f"Eroare la actualizarea statusului: {e}", "danger")

    return redirect(url_for('driver.portal'))



@driver_bp.route('/api/locations')
def api_locations():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, current_lat, current_lng FROM transport_requests WHERE status = 'In Transit'")
            jobs = cursor.fetchall()
            
            locations = [{"id": j['id'], "lat": j['current_lat'], "lng": j['current_lng']} for j in jobs]
            return jsonify(locations)
    except Exception as e:
        return jsonify([])



@driver_bp.route('/driver/support')
def support():
    if 'user_id' not in session or session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))
    
    notifications, unread_count = get_header_data()
    user_tickets = support_db.get_user_tickets(session.get('username'))
    
    return render_template('driver/support.html', 
                           tickets=user_tickets, 
                           notifications=notifications, 
                           unread_count=unread_count)

@driver_bp.route('/driver/support/create', methods=['POST'])
def create_support_ticket():
    if 'user_id' not in session or session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    username = session.get('username')
    role = str(session.get('role')).strip() 
    subject = request.form.get('subject')
    message = request.form.get('message')
    
    if subject and message:
        if support_db.create_ticket(user_id, username, subject, message, role):
             # ADMIN NOTIFICATION
             notif_db.add_notification('Administrator', f"🎧 Șoferul {username} a deschis un tichet nou.")
             notif_db.add_notification('Staff', f"🎧 Șoferul {username} a deschis un tichet nou.")
             flash("Your support ticket has been submitted.", "success")
        else:
             flash("Error submitting ticket.", "danger")
             
    return redirect(url_for('driver.support'))

@driver_bp.route('/driver/support/reply/<int:ticket_id>', methods=['POST'])
def add_ticket_reply(ticket_id):
    if 'user_id' not in session or session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))
        
    message = request.form.get('message')
    username = session.get('username')
    role = str(session.get('role')).strip() 
    
    if message:
        if support_db.add_reply(ticket_id=ticket_id, sender=username, message=message, sender_role=role):
            # ADMIN NOTIFICATION
            notif_db.add_notification('Administrator', f"💬 Șoferul {username} a răspuns la tichetul #{ticket_id}")
            notif_db.add_notification('Staff', f"💬 Șoferul {username} a răspuns la tichetul #{ticket_id}")
            flash("Reply sent successfully.", "success")
        else:
            flash("Error sending reply.", "danger")
            
    return redirect(url_for('driver.support'))

@driver_bp.route('/driver/chat/<job_id>', methods=['GET', 'POST'])
def job_chat(job_id):
    if 'user_id' not in session or session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))

    username = session.get('username')

    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            support_db.add_job_message(job_id, session['user_id'], 'Driver', message)
            
           
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    req = conn.execute("SELECT client FROM transport_requests WHERE id = ?", (job_id,)).fetchone()
                    if req and req['client']:
                        notif_db.add_notification(str(req['client']).strip(), f"💬 Șoferul {username} ți-a trimis un mesaj la cursa {job_id}")
            except Exception as e:
                logging.error(f"Eroare notificare chat sofer: {e}")
                
        return redirect(url_for('driver.job_chat', job_id=job_id))

    notifications, unread_count = get_header_data()
    messages = support_db.get_job_messages(job_id)
    
    return render_template('driver/job_chat.html', 
                           job_id=job_id, 
                           messages=messages, 
                           notifications=notifications, 
                           unread_count=unread_count)



@driver_bp.route('/drivers', methods=['GET'])
def driver_management() -> str:
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    view_data = driver_logic.load_driver_data()
    role = session.get('role', 'Staff')
    return render_template('admin/drivers.html', data=view_data, role=role)

@driver_bp.route('/drivers/add', methods=['POST'])
def add_driver() -> str:
    d_id = request.form.get('driver_id')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    status = request.form.get('status')
    exp = request.form.get('experience')
    dob = request.form.get('dob')
    doc_id = request.form.get('document_id')
    address = request.form.get('address')
    avail = request.form.get('availability')
    username = request.form.get('username')
    password = request.form.get('password')
    
    licenses_list = request.form.getlist('licenses')
    licenses_str = ", ".join(licenses_list)
    
    resp = driver_logic.add_new_driver(d_id, first_name, last_name, status, licenses_str, exp, dob, doc_id, address, avail, username, password)
    
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('driver.driver_management'))

@driver_bp.route('/drivers/edit', methods=['POST'])
def edit_driver() -> str:
    d_id = request.form.get('edit_driver_id')
    name = request.form.get('edit_name')
    status = request.form.get('edit_status')
    exp = request.form.get('edit_experience')
    dob = request.form.get('edit_dob')
    doc_id = request.form.get('edit_document_id')
    address = request.form.get('edit_address')
    avail = request.form.get('edit_availability')
    
    licenses_list = request.form.getlist('edit_licenses')
    licenses_str = ", ".join(licenses_list)
    
    resp = driver_logic.modify_driver(d_id, name, status, licenses_str, exp, dob, doc_id, address, avail)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('driver.driver_management'))

@driver_bp.route('/drivers/delete/<driver_id>', methods=['POST'])
def delete_driver(driver_id: str) -> str:
    resp = driver_logic.remove_driver(driver_id)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('driver.driver_management'))