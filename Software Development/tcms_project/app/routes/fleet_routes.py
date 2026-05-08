import logging
import sqlite3
import io
import csv
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify, make_response
from fpdf import FPDF
from app.controllers.fleet_controller import FleetController

fleet_bp = Blueprint('fleet', __name__)
fleet_logic = FleetController()

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

@fleet_bp.route('/fleet', methods=['GET'])
def fleet_management() -> str:
    if 'user_id' not in session:
        flash("Please log in to access Fleet Management.", "danger")
        return redirect(url_for('auth.login'))
    
    try:
        view_data = fleet_logic.load_fleet_data()
        user_role = session.get('role', 'Staff')
        username = session.get('username', 'User')
        
        return render_template('admin/fleet.html', data=view_data, role=user_role, username=username)
    except Exception as routing_error:
        logging.error(f"Fleet routing error: {routing_error}")
        flash("An error occurred while loading the fleet module.", "danger")
        return redirect(url_for('dashboard.main_dashboard'))

@fleet_bp.route('/fleet/add', methods=['POST'])
def add_vehicle() -> str:
    if 'user_id' not in session: return redirect(url_for('auth.login'))
        
    v_id = str(request.form.get('vehicle_id', '')).strip()
    plate = str(request.form.get('plate_number', '')).strip()
    v_type = str(request.form.get('type', '')).strip()
    status = str(request.form.get('status', '')).strip()
    capacity_str = str(request.form.get('capacity', '')).strip()
    capacity_unit = request.form.get('capacity_unit', 'kg')
    
    try:
        raw_capacity = float(capacity_str)
        final_capacity = int(raw_capacity * 1000) if capacity_unit == 'tons' else int(raw_capacity)
        modified_by = session.get('username', 'System')
        response = fleet_logic.add_new_vehicle(v_id, plate, v_type, final_capacity, status, modified_by)
        
        if response.get("success") is True: flash(response.get("message"), "success")
        else: flash(response.get("message"), "danger")
    except ValueError:
        flash("Capacity must be a valid number.", "danger")
        
    return redirect(url_for('fleet.fleet_management'))

@fleet_bp.route('/fleet/delete/<vehicle_id>', methods=['POST'])
def delete_vehicle(vehicle_id: str) -> str:
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    modified_by = session.get('username', 'System')
    response = fleet_logic.remove_vehicle(vehicle_id, modified_by)
    flash(response.get("message"), "success" if response.get("success") else "danger")
    return redirect(url_for('fleet.fleet_management'))

@fleet_bp.route('/fleet/edit', methods=['POST'])
def edit_vehicle() -> str:
    if 'user_id' not in session: return redirect(url_for('auth.login'))
        
    v_id = str(request.form.get('edit_vehicle_id', '')).strip()
    plate = str(request.form.get('edit_plate_number', '')).strip()
    v_type = str(request.form.get('edit_type', '')).strip()
    status = str(request.form.get('edit_status', '')).strip()
    capacity_str = str(request.form.get('edit_capacity', '')).strip()
    capacity_unit = request.form.get('edit_capacity_unit', 'kg')
    
    try:
        raw_capacity = float(capacity_str)
        final_capacity = int(raw_capacity * 1000) if capacity_unit == 'tons' else int(raw_capacity)
        modified_by = session.get('username', 'System')
        response = fleet_logic.modify_vehicle(v_id, plate, v_type, final_capacity, status, modified_by)
        
        flash(response.get("message"), "success" if response.get("success") else "danger")
    except ValueError:
        flash("Capacity must be a valid number.", "danger")
        
    return redirect(url_for('fleet.fleet_management'))

@fleet_bp.route('/fleet/export/<file_type>')
def export_fleet(file_type: str):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    vehicles = fleet_logic.model.get_all_vehicles()
    headers = ['Vehicle ID', 'Plate Number', 'Vehicle Type', 'Capacity (kg)', 'Status']
    data_rows = [[remove_diacritics(str(v['id'])), remove_diacritics(str(v['plate_number'])), remove_diacritics(str(v['type'])), str(v['capacity']), remove_diacritics(str(v['status']))] for v in vehicles]
    
    if file_type == 'pdf':
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, txt="TRANSPORT COMPANY - FLEET REGISTRY", ln=True, align='C')
        pdf.ln(10)
        
        col_widths = [35, 40, 40, 40, 35]
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
        response.headers["Content-Disposition"] = "attachment; filename=Fleet_Registry.pdf"
        response.headers["Content-type"] = "application/pdf"
        return response

    elif file_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        writer.writerows(data_rows)
        response = make_response(output.getvalue().encode('utf-8-sig'))
        response.headers["Content-Disposition"] = "attachment; filename=Fleet_Registry.csv"
        response.headers["Content-type"] = "text/csv; charset=utf-8-sig"
        return response

    elif file_type == 'txt':
        content = "=== FLEET REGISTRY ===\n\n"
        content += " | ".join(headers) + "\n" + "-" * 70 + "\n"
        for row in data_rows:
            content += " | ".join(row) + "\n"
        response = make_response(content)
        response.headers["Content-Disposition"] = "attachment; filename=Fleet_Registry.txt"
        response.headers["Content-type"] = "text/plain"
        return response

    return redirect(url_for('fleet.fleet_management'))

@fleet_bp.route('/api/live_fleet')
def live_fleet_api():
    try:
        with sqlite3.connect("instance/database.sqlite") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Preluam acum si vehicle_type din baza de date
            cursor.execute("SELECT id, current_lat, current_lng, pickup, delivery, saved_route, vehicle_type FROM transport_requests WHERE status = 'In Transit'")
            jobs = cursor.fetchall()
            
            locations = []
            for j in jobs:
                locations.append({
                    "id": j['id'],
                    "lat": j['current_lat'],
                    "lng": j['current_lng'],
                    "pickup": j['pickup'],
                    "delivery": j['delivery'],
                    "saved_route": j['saved_route'],
                    "vehicle_type": j['vehicle_type'] # Trimitem tipul pentru randarea hartii
                })
            return jsonify(locations)
    except Exception as e:
        logging.error(f"Eroare API Live Fleet: {e}")
        return jsonify([])

@fleet_bp.route('/api/save_route', methods=['POST'])
def save_route_api():
    data = request.get_json()
    req_id = data.get('req_id')
    route_json = data.get('route')
    try:
        with sqlite3.connect("instance/database.sqlite") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE transport_requests SET saved_route = ? WHERE id = ?", (route_json, req_id))
            conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500