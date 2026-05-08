import sqlite3
import logging
import io
import csv
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify, make_response
from fpdf import FPDF
from app.controllers.driver_portal_controller import DriverPortalController
from app.controllers.driver_controller import DriverController
from app.models.support_model import SupportModel 
from app.models.notification_model import NotificationModel

driver_bp = Blueprint('driver', __name__)
driver_logic = DriverController()
driver_portal_logic = DriverPortalController()
support_db = SupportModel() 
notif_db = NotificationModel()

try:
    notif_db.create_table()
except:
    pass

DB_PATH = "instance/database.sqlite"

def remove_diacritics(text: str) -> str:
    if not text: return ""
    replacements = {
        'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
        'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T',
        'ş': 's', 'ţ': 't', 'Ş': 'S', 'Ţ': 'T',
        'ã': 'a', 'Ã': 'A'
    }
    res = str(text)
    for ro_char, eng_char in replacements.items():
        res = res.replace(ro_char, eng_char)
    return res.encode('latin-1', 'replace').decode('latin-1')

def render_pdf_row(pdf, row_data, col_widths, line_height=6):
    max_lines = 1
    for i, text in enumerate(row_data):
        text_str = str(text)
        text_width = pdf.get_string_width(text_str)
        lines_by_width = int(text_width / (col_widths[i] - 3)) + 1
        lines_by_newline = text_str.count('\n') + 1
        lines = max(lines_by_width, lines_by_newline)
        if lines > max_lines: max_lines = lines
    row_height = max_lines * line_height
    if pdf.get_y() + row_height > 275: pdf.add_page()
    x_start = pdf.get_x()
    y_start = pdf.get_y()
    for i, text in enumerate(row_data):
        pdf.set_xy(x_start, y_start)
        pdf.rect(x_start, y_start, col_widths[i], row_height)
        pdf.multi_cell(col_widths[i], line_height, str(text), border=0, align='C')
        x_start += col_widths[i]
    pdf.set_xy(pdf.l_margin, y_start + row_height)

def get_header_data():
    username = str(session.get('username', '')).strip()
    role = str(session.get('role', 'Driver')).strip()
    try:
        notifications = notif_db.get_unread_notifications(username, role)
        unread_count = len(notifications)
    except Exception as e:
        logging.error(f"Error fetching notifications: {e}")
        notifications = []
        unread_count = 0
    return notifications, unread_count

# ========================================================
# DRIVER PORTAL & HISTORY ROUTES
# ========================================================

@driver_bp.route('/driver_portal')
def portal():
    if 'user_id' not in session or session.get('role') != 'Driver':
        flash("Access denied. Drivers only.", "danger")
        return redirect(url_for('auth.login'))
        
    username = session.get('username')
    notifications, unread_count = get_header_data()
    
    # MAGIC: Controller-ul se ocupa de toata logica anti-fail!
    data = driver_portal_logic.load_dashboard_data(username)
    
    return render_template('driver/portal.html', data=data, notifications=notifications, unread_count=unread_count)

@driver_bp.route('/driver/history')
def history():
    if 'user_id' not in session or session.get('role') != 'Driver': 
        return redirect(url_for('auth.login'))
        
    username = session.get('username')
    notifications, unread_count = get_header_data()
    
    # Aduce absolut toate cursele care sunt "Delivered" pentru soferul tau
    jobs = driver_portal_logic.load_history_data(username)
    return render_template('driver/history.html', jobs=jobs, notifications=notifications, unread_count=unread_count)

@driver_bp.route('/driver_portal/update_status/<job_id>/<new_status>', methods=['POST'])
def update_job_status(job_id, new_status):
    if 'user_id' not in session or session.get('role') != 'Driver': return redirect(url_for('auth.login'))
    response = driver_portal_logic.update_job_status(job_id, new_status)
    flash(response['message'], "success" if response['success'] else "danger")
    return redirect(url_for('driver.portal'))

@driver_bp.route('/driver_portal/update_vehicle_status', methods=['POST'])
def update_vehicle_status():
    if 'user_id' not in session or session.get('role') != 'Driver': return redirect(url_for('auth.login'))
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
            
        alert_icon = "🟢" if new_status == 'Active' else "⚠️"
        admin_msg = f"{alert_icon} Șoferul {driver_name} a schimbat statusul vehiculului în: {new_status}."
        notif_db.add_notification('Administrator', admin_msg)
        notif_db.add_notification('Staff', admin_msg)
        flash(f"Statusul mașinii a fost actualizat la: {new_status}.", "success")
    except Exception as e:
        flash(f"Eroare la actualizarea statusului: {e}", "danger")
    return redirect(url_for('driver.portal'))

# ========================================================
# SUPPORT & CHAT ROUTES
# ========================================================

@driver_bp.route('/driver/support')
def support():
    if 'user_id' not in session or session.get('role') != 'Driver': return redirect(url_for('auth.login'))
    notifications, unread_count = get_header_data()
    user_tickets = support_db.get_user_tickets(session.get('username'))
    return render_template('driver/support.html', tickets=user_tickets, notifications=notifications, unread_count=unread_count)

@driver_bp.route('/driver/support/create', methods=['POST'])
def create_support_ticket():
    if 'user_id' not in session or session.get('role') != 'Driver': return redirect(url_for('auth.login'))
    user_id = session.get('user_id')
    username = session.get('username')
    role = str(session.get('role')).strip() 
    subject = request.form.get('subject')
    message = request.form.get('message')
    if subject and message:
        if support_db.create_ticket(user_id, username, subject, message, role):
             notif_db.add_notification('Administrator', f"🎧 Șoferul {username} a deschis un tichet.")
             notif_db.add_notification('Staff', f"🎧 Șoferul {username} a deschis un tichet.")
             flash("Your support ticket has been submitted.", "success")
        else: flash("Error submitting ticket.", "danger")
    return redirect(url_for('driver.support'))

@driver_bp.route('/driver/support/reply/<int:ticket_id>', methods=['POST'])
def add_ticket_reply(ticket_id):
    if 'user_id' not in session or session.get('role') != 'Driver': return redirect(url_for('auth.login'))
    message = request.form.get('message')
    username = session.get('username')
    role = str(session.get('role')).strip() 
    if message:
        if support_db.add_reply(ticket_id=ticket_id, sender=username, message=message, sender_role=role):
            notif_db.add_notification('Administrator', f"💬 Șoferul {username} a răspuns la tichetul #{ticket_id}")
            notif_db.add_notification('Staff', f"💬 Șoferul {username} a răspuns la tichetul #{ticket_id}")
            flash("Reply sent successfully.", "success")
        else: flash("Error sending reply.", "danger")
    return redirect(url_for('driver.support'))

@driver_bp.route('/driver/chat/<job_id>', methods=['GET', 'POST'])
def job_chat(job_id):
    if 'user_id' not in session or session.get('role') != 'Driver': return redirect(url_for('auth.login'))
    username = session.get('username')
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            support_db.add_job_message(job_id, session['user_id'], 'Driver', message)
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    req = conn.execute("SELECT client FROM transport_requests WHERE id = ?", (job_id,)).fetchone()
                    if req and req['client']: notif_db.add_notification(str(req['client']).strip(), f"💬 Șoferul {username} ți-a trimis un mesaj la cursa {job_id}")
            except Exception as e: logging.error(f"Eroare notificare chat sofer: {e}")
        return redirect(url_for('driver.job_chat', job_id=job_id))
    notifications, unread_count = get_header_data()
    messages = support_db.get_job_messages(job_id)
    return render_template('driver/job_chat.html', job_id=job_id, messages=messages, notifications=notifications, unread_count=unread_count, username=username)

# ========================================================
# ADMIN: DRIVERS MANAGEMENT ROUTES
# ========================================================

@driver_bp.route('/drivers', methods=['GET'])
def driver_management() -> str:
    if 'user_id' not in session: return redirect(url_for('auth.login'))
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
    address = request.form.get('address')
    avail = request.form.get('availability')
    username = request.form.get('username')
    password = request.form.get('password')
    licenses_str = ", ".join(request.form.getlist('licenses'))
    modified_by = session.get('username', 'System')
    resp = driver_logic.add_new_driver(d_id, first_name, last_name, status, licenses_str, exp, dob, address, avail, username, password, modified_by)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('driver.driver_management'))

@driver_bp.route('/drivers/edit', methods=['POST'])
def edit_driver() -> str:
    d_id = request.form.get('edit_driver_id')
    first_name = request.form.get('edit_first_name')
    last_name = request.form.get('edit_last_name')
    status = request.form.get('edit_status')
    exp = request.form.get('edit_experience')
    dob = request.form.get('edit_dob')
    address = request.form.get('edit_address')
    avail = request.form.get('edit_availability')
    licenses_str = ", ".join(request.form.getlist('edit_licenses'))
    modified_by = session.get('username', 'System')
    resp = driver_logic.modify_driver(d_id, first_name, last_name, status, licenses_str, exp, dob, address, avail, modified_by)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('driver.driver_management'))

@driver_bp.route('/drivers/delete/<driver_id>', methods=['POST'])
def delete_driver(driver_id: str) -> str:
    modified_by = session.get('username', 'System')
    resp = driver_logic.remove_driver(driver_id, modified_by)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('driver.driver_management'))

@driver_bp.route('/drivers/export/<file_type>')
def export_drivers(file_type: str):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    drivers_data = driver_logic.load_driver_data()
    drivers = drivers_data.get('drivers', [])
    headers = ['System ID', 'Driver Name', 'Licenses', 'Availability', 'Status']
    data_rows = [[remove_diacritics(str(d['id'])), remove_diacritics(str(d['name'])), remove_diacritics(str(d['licenses'])), remove_diacritics(str(d['availability'])), remove_diacritics(str(d['status']))] for d in drivers]
    
    if file_type == 'pdf':
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, txt="TRANSPORT COMPANY - DRIVER REGISTRY", ln=True, align='C')
        pdf.ln(10)
        
        col_widths = [35, 45, 50, 35, 25]
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(0, 120, 212)
        pdf.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 8, str(h), border=1, fill=True, align='C')
        pdf.ln(8)

        pdf.set_font("Arial", '', 9)
        pdf.set_text_color(0, 0, 0)
        for row in data_rows:
            render_pdf_row(pdf, row, col_widths)

        response = make_response(pdf.output(dest='S').encode('latin-1'))
        response.headers["Content-Disposition"] = "attachment; filename=Drivers_Registry.pdf"
        response.headers["Content-type"] = "application/pdf"
        return response

    elif file_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        writer.writerows(data_rows)
        response = make_response(output.getvalue().encode('utf-8-sig'))
        response.headers["Content-Disposition"] = "attachment; filename=Drivers_Registry.csv"
        response.headers["Content-type"] = "text/csv; charset=utf-8-sig"
        return response

    elif file_type == 'txt':
        content = "=== DRIVER REGISTRY ===\n\n"
        content += " | ".join(headers) + "\n" + "-" * 70 + "\n"
        for row in data_rows:
            content += " | ".join(row) + "\n"
        response = make_response(content)
        response.headers["Content-Disposition"] = "attachment; filename=Drivers_Registry.txt"
        response.headers["Content-type"] = "text/plain"
        return response

    return redirect(url_for('driver.driver_management'))