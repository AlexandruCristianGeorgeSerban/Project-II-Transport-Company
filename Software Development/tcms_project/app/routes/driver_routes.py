import sqlite3
import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.controllers.driver_portal_controller import DriverPortalController
from app.controllers.driver_controller import DriverController
from app.models.fleet_model import FleetModel
from app.models.support_model import SupportModel 
from app.models.notification_model import NotificationModel

driver_bp = Blueprint('driver', __name__)
driver_logic = DriverController()
driver_portal_logic = DriverPortalController()
support_db = SupportModel() 
notif_db = NotificationModel()

DB_PATH = "instance/database.sqlite"

def get_header_data():
    """Aduce notificările și numărul lor pentru clopoțelul din meniul de sus."""
    role = session.get('role', 'Driver')
    try:
        notifications = notif_db.get_unread_notifications(role)
        unread_count = len(notifications)
    except Exception as e:
        logging.error(f"Error fetching notifications: {e}")
        notifications = []
        unread_count = 0
    return notifications, unread_count

def get_driver_jobs(user_id, username, status_type='active'):
    """Incarcă joburile reale făcând o punte inteligentă între tabelul users și drivers."""
    jobs = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if status_type == 'active':
                query = """
                    SELECT * FROM transport_requests 
                    WHERE (
                        CAST(driver_id AS TEXT) = ? 
                        OR CAST(driver_id AS TEXT) = ? 
                        OR CAST(driver_id AS TEXT) IN (SELECT CAST(id AS TEXT) FROM drivers WHERE name = ?)
                    ) 
                    AND status != 'Delivered'
                """
            else:
                query = """
                    SELECT * FROM transport_requests 
                    WHERE (
                        CAST(driver_id AS TEXT) = ? 
                        OR CAST(driver_id AS TEXT) = ? 
                        OR CAST(driver_id AS TEXT) IN (SELECT CAST(id AS TEXT) FROM drivers WHERE name = ?)
                    ) 
                    AND status = 'Delivered'
                """
            
            cursor.execute(query, (str(user_id), str(username), str(username)))
            jobs = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Database error in driver_routes: {e}")
    return jobs

# ==========================================
# RUTE PORTAL ȘI JOBURI ACTIVE
# ==========================================

@driver_bp.route('/driver_portal')
def portal():
    if 'user_id' not in session or session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))
        
    driver_id = session.get('user_id')
    
    data = driver_portal_logic.load_dashboard_data(driver_id)
    
    return render_template('driver/portal.html', data=data)

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

    if not vehicle_id or not new_status:
         flash("Eroare la preluarea datelor vehiculului.", "danger")
         return redirect(url_for('driver.portal'))
    
    try:
        with sqlite3.connect(DB_PATH) as connection:
            db_cursor = connection.cursor()
            db_cursor.execute("UPDATE vehicles SET status = ? WHERE id = ?", (new_status, vehicle_id))
            connection.commit()
            flash(f"Statusul mașinii a fost actualizat la: {new_status}", "success")
    except Exception as e:
        flash(f"Eroare la actualizarea statusului: {e}", "danger")

    return redirect(url_for('driver.portal'))

# ==========================================
# RUTE CHAT ȘI SUPPORT
# ==========================================

@driver_bp.route('/driver/support')
def support():
    if 'user_id' not in session or session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))
    
    notifications, unread_count = get_header_data()
    # AICI E MAGIA: Folosim username-ul pentru a gasi tichetele corect in baza de date!
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
    # Extragem rolul si il curatam de orice spatiu gol accidental
    role = str(session.get('role')).strip() 
    subject = request.form.get('subject')
    message = request.form.get('message')
    
    if subject and message:
        # Trimitem rolul (Driver) catre baza de date
        if support_db.create_ticket(user_id, username, subject, message, role):
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
        # REPARATIE IDENTICA: Specificam clar cine e cine
        if support_db.add_reply(ticket_id=ticket_id, sender=username, message=message, sender_role=role):
            flash("Reply sent successfully.", "success")
        else:
            flash("Error sending reply.", "danger")
            
    return redirect(url_for('driver.support'))

@driver_bp.route('/driver/chat/<job_id>', methods=['GET', 'POST'])
def job_chat(job_id):
    if 'user_id' not in session or session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            support_db.add_job_message(job_id, session['user_id'], 'Driver', message)
        return redirect(url_for('driver.job_chat', job_id=job_id))

    notifications, unread_count = get_header_data()
    messages = support_db.get_job_messages(job_id)
    
    return render_template('driver/job_chat.html', 
                           job_id=job_id, 
                           messages=messages, 
                           notifications=notifications, 
                           unread_count=unread_count)

# ==========================================
# RUTE MANAGEMENT ADMIN PENTRU SOFERI
# ==========================================

@driver_bp.route('/drivers', methods=['GET'])
def driver_management() -> str:
    """Renders the main Driver Management page."""
    if 'user_id' not in session:
        flash("Please log in.", "danger")
        return redirect(url_for('auth.login'))
    
    view_data = driver_logic.load_driver_data()
    role = session.get('role', 'Staff')
    
    return render_template('admin/drivers.html', data=view_data, role=role)

@driver_bp.route('/drivers/add', methods=['POST'])
def add_driver() -> str:
    # Extragem informatiile angajatului
    d_id = request.form.get('driver_id')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    status = request.form.get('status')
    exp = request.form.get('experience')
    dob = request.form.get('dob')
    doc_id = request.form.get('document_id')
    address = request.form.get('address')
    avail = request.form.get('availability')
    
    # Extragem datele contului de conectare
    username = request.form.get('username')
    password = request.form.get('password')
    
    licenses_list = request.form.getlist('licenses')
    licenses_str = ", ".join(licenses_list)
    
    resp = driver_logic.add_new_driver(d_id, first_name, last_name, status, licenses_str, exp, dob, doc_id, address, avail, username, password)
    
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('driver.driver_management'))

@driver_bp.route('/drivers/edit', methods=['POST'])
def edit_driver() -> str:
    """Handles editing a driver."""
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
    """Handles deleting a driver."""
    resp = driver_logic.remove_driver(driver_id)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('driver.driver_management'))