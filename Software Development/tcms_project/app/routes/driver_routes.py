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

def get_driver_jobs(user_id, username, status_type='active'):
    jobs = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if status_type == 'active':
                query = "SELECT * FROM transport_requests WHERE (driver_id = ? OR driver_id = ?) AND status != 'Delivered'"
            else:
                query = "SELECT * FROM transport_requests WHERE (driver_id = ? OR driver_id = ?) AND status = 'Delivered'"
            
            cursor.execute(query, (str(user_id), str(username)))
            jobs = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Database error in driver_routes: {e}")
    return jobs

# ========================================================
# DRIVER PORTAL & HISTORY ROUTES
# ========================================================

@driver_bp.route('/driver_portal')
@driver_bp.route('/driver/portal')
def portal():
    if 'user_id' not in session or session.get('role') != 'Driver':
        flash("Access denied. Drivers only.", "danger")
        return redirect(url_for('auth.login'))
        
    username = session.get('username')
    notifications, unread_count = get_header_data()
    data = driver_portal_logic.load_dashboard_data(username)
    return render_template('driver/portal.html', data=data, notifications=notifications, unread_count=unread_count)

@driver_bp.route('/driver/history')
def history():
    if 'user_id' not in session or session.get('role') != 'Driver': 
        return redirect(url_for('auth.login'))
        
    username = session.get('username')
    notifications, unread_count = get_header_data()
    jobs = driver_portal_logic.load_history_data(username)
    return render_template('driver/history.html', jobs=jobs, notifications=notifications, unread_count=unread_count)

@driver_bp.route('/driver_portal/update_status/<job_id>/<new_status>', methods=['POST'])
@driver_bp.route('/driver/update_status/<job_id>/<new_status>', methods=['POST'])
def update_job_status(job_id, new_status):
    if 'user_id' not in session or session.get('role') != 'Driver': return redirect(url_for('auth.login'))
    driver_name = session.get('username', 'Driver')
    response = driver_portal_logic.update_job_status(job_id, new_status, driver_username=driver_name)
    flash(response['message'], "success" if response['success'] else "danger")
    return redirect(url_for('driver.portal'))

@driver_bp.route('/driver_portal/update_vehicle_status', methods=['POST'])
def update_vehicle_status():
    if 'user_id' not in session or session.get('role') != 'Driver': return redirect(url_for('auth.login'))
    vehicle_id = request.form.get('vehicle_id')
    new_status = request.form.get('status')
    driver_name = session.get('username', 'Driver')
    if not vehicle_id:
        flash("Eroare: Vehicul negăsit.", "danger")
        return redirect(url_for('driver.portal'))
    
    resp = driver_portal_logic.set_vehicle_status(vehicle_id, new_status, driver_username=driver_name)
    if resp.get("success"):
        alert_icon = "🟢" if new_status == 'Available' else "⚠️"
        admin_msg = f"{alert_icon} Șoferul {driver_name} a schimbat statusul vehiculului ({vehicle_id}) în: {new_status}."
        notif_db.add_notification('Administrator', admin_msg, target_url="/fleet")
        notif_db.add_notification('Staff', admin_msg, target_url="/fleet")
        flash(f"Statusul mașinii a fost actualizat la: {new_status}.", "success")
    else:
        flash("Eroare la actualizarea statusului.", "danger")
    return redirect(url_for('driver.portal'))

# ========================================================
# SUPPORT & CHAT ROUTES
# ========================================================

@driver_bp.route('/driver/support')
def support():
    if 'user_id' not in session or session.get('role') != 'Driver': return redirect(url_for('auth.login'))
    notifications, unread_count = get_header_data()
    username = session.get('username')
    user_tickets = support_db.get_user_tickets(username)
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
            notif_db.add_notification('Administrator', f"🎧 Șoferul {username} a deschis un tichet.", target_url="/admin/support")
            notif_db.add_notification('Staff', f"🎧 Șoferul {username} a deschis un tichet.", target_url="/admin/support")
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
            admin_target = url_for('admin_support.view_tickets') + f"#ticket-{ticket_id}"
            notif_db.add_notification('Administrator', f"💬 Șoferul {username} a răspuns la tichetul #{ticket_id}", target_url=admin_target)
            notif_db.add_notification('Staff', f"💬 Șoferul {username} a răspuns la tichetul #{ticket_id}", target_url=admin_target)
            flash("Reply sent successfully.", "success")
        else: flash("Error sending reply.", "danger")
    return redirect(url_for('driver.support'))

@driver_bp.route('/driver/chat/<job_id>', methods=['GET', 'POST'])
def job_chat(job_id):
    job_id = str(job_id).upper()
    
    if 'user_id' not in session or session.get('role') != 'Driver': 
        flash("Access denied. Private Driver chat.", "danger")
        return redirect(url_for('dashboard.main_dashboard'))
        
    username = session.get('username')
    role = 'Driver'
    
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            support_db.add_job_message(job_id, session['user_id'], role, message)
            try:
                with sqlite3.connect("instance/database.sqlite") as conn:
                    conn.row_factory = sqlite3.Row
                    req = conn.execute("SELECT client FROM transport_requests WHERE id = ?", (job_id,)).fetchone()
                    if req and req['client']: 
                        target_client = str(req['client']).strip()
                        if target_client != username:
                            target_url = f"/customer/chat/{job_id}"
                            notif_db.add_notification(target_client, f"💬 Șoferul {username} ți-a scris la cursa {job_id}", target_url=target_url)
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
    form_data = request.form.to_dict()
    logging.warning(f"[ADD DRIVER] Formul a trimis următoarele date: {form_data}")
    
    d_id = form_data.get('driver_id', '')
    
    f_name = form_data.get('first_name', '').strip()
    l_name = form_data.get('last_name', '').strip()
    single_name = form_data.get('name', '').strip() or form_data.get('driver_name', '').strip() or form_data.get('full_name', '').strip()
    
    if f_name or l_name:
        name = f"{f_name} {l_name}".strip()
    elif single_name:
        name = single_name
    else:
        name = "Nume Lipsă (Verifică HTML!)"
        
    status = form_data.get('status', 'Active')
    exp = form_data.get('experience', '1 Year')
    dob = form_data.get('dob', '2000-01-01')
    address = form_data.get('address', 'Unknown')
    avail = form_data.get('availability', 'Available')
    username = form_data.get('username')
    password = form_data.get('password')
    
    # 📧 PRELUĂM EMAIL-UL AICI
    email = form_data.get('email', None)
    if email == "":
         email = None
    
    licenses_list = request.form.getlist('licenses')
    licenses_str = ", ".join(licenses_list)
    modified_by = session.get('username', 'System')
    
    resp = driver_logic.add_new_driver(d_id, name, status, licenses_str, exp, dob, address, avail, email, username, password, modified_by=modified_by)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('driver.driver_management'))

@driver_bp.route('/drivers/edit', methods=['POST'])
def edit_driver() -> str:
    form_data = request.form.to_dict()
    logging.warning(f"[EDIT DRIVER] Formul a trimis următoarele date: {form_data}")
    
    d_id = form_data.get('edit_driver_id', '') or form_data.get('driver_id', '')
    
    f_name = form_data.get('edit_first_name', '').strip() or form_data.get('first_name', '').strip()
    l_name = form_data.get('edit_last_name', '').strip() or form_data.get('last_name', '').strip()
    single_name = form_data.get('edit_name', '').strip() or form_data.get('name', '').strip() or form_data.get('driver_name', '').strip()
    
    if f_name or l_name:
        name = f"{f_name} {l_name}".strip()
    elif single_name:
        name = single_name
    else:
        name = "Nume Lipsă (Verifică HTML!)"

    status = form_data.get('edit_status') or form_data.get('status')
    exp = form_data.get('edit_experience') or form_data.get('experience')
    dob = form_data.get('edit_dob') or form_data.get('dob')
    address = form_data.get('edit_address') or form_data.get('address')
    avail = form_data.get('edit_availability') or form_data.get('availability')
    
    licenses_list = request.form.getlist('edit_licenses')
    if not licenses_list:
        licenses_list = request.form.getlist('licenses')
    licenses_str = ", ".join(licenses_list)
    
    modified_by = session.get('username', 'System')
    
    resp = driver_logic.modify_driver(d_id, name, status, licenses_str, exp, dob, address, avail, modified_by=modified_by)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('driver.driver_management'))

@driver_bp.route('/drivers/delete/<driver_id>', methods=['POST'])
def delete_driver(driver_id: str) -> str:
    modified_by = session.get('username', 'System')
    resp = driver_logic.remove_driver(driver_id, modified_by=modified_by)
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

@driver_bp.route('/purge_all_drivers')
def purge_all_drivers():
    """Ruta pentru stergerea ABSOLUT TUTUROR conturilor de șofer din tabelul de users."""
    try:
        import sqlite3
        with sqlite3.connect("instance/database.sqlite") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE role = 'Driver'")
            deleted_count = cursor.rowcount
            conn.commit()
            return f"<h1>🧹 CURĂȚENIE TOTALĂ (Thanos Snap) 💥</h1><p>Am evaporat <b>{deleted_count}</b> conturi fantomă de șoferi din sistem!</p><p>Niciun cont vechi (nici ship, nici driver) nu mai funcționează.</p> <a href='/login'>Du-te la login și verifică.</a>"
    except Exception as e:
        return f"Eroare la curățenie: {e}"

@driver_bp.route('/inspect_db')
def inspect_db():
    """Ruta care ne arata exact ce conturi mai exista in baza noastra de date."""
    try:
        import sqlite3
        with sqlite3.connect("instance/database.sqlite") as conn:
            conn.row_factory = sqlite3.Row
            users = conn.execute("SELECT id, username, role FROM users").fetchall()
            
            html = "<h1>🕵️‍♂️ Lista tuturor conturilor din 'database.sqlite':</h1><table border='1' cellpadding='10'><tr><th>ID</th><th>Username</th><th>Rol</th></tr>"
            for u in users:
                html += f"<tr><td>{u['id']}</td><td>{u['username']}</td><td>{u['role']}</td></tr>"
            html += "</table>"
            return html
    except Exception as e:
        return f"Eroare: {e}"    

@driver_bp.route('/total_clean_up')
def total_clean_up():
    """Șterge manual toate conturile fantomă găsite în inspect_db."""
    ghosts = [
        'ship', 'driver', '77', '123', 'testare', 
        '234', 'd2', 'd3', 'd5', 'd6', '24', 
        'shippy', 'popa', '12'
    ]
    try:
        import sqlite3
        with sqlite3.connect("instance/database.sqlite") as conn:
            cursor = conn.cursor()
            
            placeholders = ', '.join(['?'] * len(ghosts))
            query = "DELETE FROM users WHERE username IN (" + placeholders + ")"
            cursor.execute(query, ghosts)
            users_deleted = cursor.rowcount
            
            cursor.execute("DELETE FROM drivers")
            drivers_deleted = cursor.rowcount
            
            conn.commit()
            
            return f"""
            <h1>🧹 Operațiunea 'Mătura' Finalizată!</h1>
            <p>Utilizatori (Users) rasi: <b>{users_deleted}</b></p>
            <p>Fișe logistice (Drivers) șterse: <b>{drivers_deleted}</b></p>
            <hr>
            <p><b>Au rămas doar:</b> Administrator (11), Staff (66) și Clienții (22, adonis).</p>
            <a href='/inspect_db'>Verifică din nou lista aici</a>
            """
    except Exception as e:
        return f"Eroare la curățenie: {e}"
