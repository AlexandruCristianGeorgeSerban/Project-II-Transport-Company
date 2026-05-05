import logging
import sqlite3
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.controllers.driver_controller import DriverController
from app.models.support_model import SupportModel 
from app.models.notification_model import NotificationModel

driver_bp = Blueprint('driver', __name__)
driver_logic = DriverController()
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
    """Incarcă joburile reale din baza de date bazat pe driver_id."""
    jobs = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            
            
            if status_type == 'active':
                query = """
                    SELECT * FROM transport_requests 
                    WHERE (driver_id = ? OR driver_id = ?) 
                    AND status != 'Delivered'
                """
            else:
                query = """
                    SELECT * FROM transport_requests 
                    WHERE (driver_id = ? OR driver_id = ?) 
                    AND status = 'Delivered'
                """
            
            cursor.execute(query, (str(user_id), str(username)))
            jobs = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Database error in driver_routes: {e}")
    return jobs



@driver_bp.route('/driver/portal')
@driver_bp.route('/active_jobs') 
def portal():
    if 'user_id' not in session or session.get('role') != 'Driver':
        flash("Access denied. Drivers only.", "danger")
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    username = session.get('username')
    
    notifications, unread_count = get_header_data()
    jobs = get_driver_jobs(user_id, username, 'active')
    
    return render_template('driver/portal.html', 
                           jobs=jobs, 
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

@driver_bp.route('/driver/update_status/<req_id>/<new_status>', methods=['POST'])
def update_status(req_id, new_status):
    if 'user_id' not in session or session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("UPDATE transport_requests SET status = ? WHERE id = ?", (new_status, req_id))
            conn.commit()
            flash(f"Status updated to {new_status}!", "success")
    except Exception as e:
        logging.error(f"Error updating status: {e}")
        flash("Error updating status.", "danger")
        
    return redirect(url_for('driver.portal'))



@driver_bp.route('/driver/support')
def support():
    if 'user_id' not in session or session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))
    
    notifications, unread_count = get_header_data()
    user_tickets = support_db.get_user_tickets(session.get('user_id'))
    
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
    subject = request.form.get('subject')
    message = request.form.get('message')
    
    if subject and message:
        if support_db.create_ticket(user_id, username, subject, message):
             flash("Your support ticket has been submitted.", "success")
        else:
             flash("Error submitting ticket.", "danger")
             
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
    name = request.form.get('name')
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
    
    
    resp = driver_logic.add_new_driver(d_id, name, status, licenses_str, exp, dob, doc_id, address, avail, username, password)
    
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