import io
import csv
import sqlite3
import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, make_response
from fpdf import FPDF
from app.controllers.report_controller import ReportController

report_bp = Blueprint('report_routes', __name__)
report_logic = ReportController()
DB_PATH = "instance/database.sqlite"

def remove_diacritics(text: str) -> str:
    """Înlocuiește TOATE variantele de diacritice românești pentru a preveni erorile '?' din FPDF."""
    if not text:
        return ""
    replacements = {
        'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
        'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T',
        'ş': 's', 'ţ': 't', 'Ş': 'S', 'Ţ': 'T',  # Inclusiv variantele cu sedilă
        'ã': 'a', 'Ã': 'A'
    }
    res = str(text)
    for ro_char, eng_char in replacements.items():
        res = res.replace(ro_char, eng_char)
    # Trecem printr-un filtru de siguranță pentru alte caractere ciudate
    return res.encode('latin-1', 'replace').decode('latin-1')

def render_pdf_row(pdf, row_data, col_widths, line_height=6):
    """Randează un rând în PDF care se ajustează automat pe mai multe linii dacă textul este prea lung."""
    max_lines = 1
    # Calculăm de câte linii este nevoie pentru textul cel mai lung din rând
    for i, text in enumerate(row_data):
        text_str = str(text)
        text_width = pdf.get_string_width(text_str)
        lines_by_width = int(text_width / (col_widths[i] - 3)) + 1
        lines_by_newline = text_str.count('\n') + 1
        lines = max(lines_by_width, lines_by_newline)
        if lines > max_lines:
            max_lines = lines
            
    row_height = max_lines * line_height
    
    # Dacă nu e loc pe pagină, trecem la pagina următoare
    if pdf.get_y() + row_height > 275:
        pdf.add_page()
        
    x_start = pdf.get_x()
    y_start = pdf.get_y()
    
    # Desenăm fiecare celulă cu multi_cell (care mută textul pe rândul următor automat)
    for i, text in enumerate(row_data):
        pdf.set_xy(x_start, y_start)
        pdf.rect(x_start, y_start, col_widths[i], row_height)
        pdf.multi_cell(col_widths[i], line_height, str(text), border=0, align='L')
        x_start += col_widths[i]
        
    # Punem cursorul sub rândul tocmai desenat
    pdf.set_xy(pdf.l_margin, y_start + row_height)

@report_bp.route('/reports', methods=['GET'])
def reports_management() -> str:
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    view_data = report_logic.load_reports_history()
    role = session.get('role', 'Staff')
    return render_template('admin/reports.html', data=view_data, role=role)

@report_bp.route('/reports/generate', methods=['POST'])
def generate_report() -> str:
    r_type = request.form.get('report_type')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    user = session.get('username', 'Admin')
    
    resp = report_logic.generate_new_report(r_type, start_date, end_date, user)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('report_routes.reports_management'))

@report_bp.route('/reports/download/<report_id>/<file_type>')
def download_report(report_id: str, file_type: str):
    report = report_logic.model.get_report_by_id(report_id)
    if not report:
        flash("Report not found.", "danger")
        return redirect(url_for('report_routes.reports_management'))

    clean_report_name = remove_diacritics(report['name'])
    filename = f"Report_{report_id}_{report['type'].replace(' ', '_')}"

    actual_headers = []
    actual_data = []
    col_widths = []

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            if report['type'] == 'Usage':
                cursor.execute("SELECT plate_number, type, capacity, status FROM vehicles")
                actual_headers = ['Plate Number', 'Vehicle Type', 'Capacity (kg)', 'Status']
                col_widths = [45, 45, 45, 55] 
                for row in cursor.fetchall():
                    actual_data.append([
                        remove_diacritics(str(row[0])), 
                        remove_diacritics(str(row[1])), 
                        remove_diacritics(str(row[2])), 
                        remove_diacritics(str(row[3]))
                    ])
                
            elif report['type'] == 'Activity':
                cursor.execute("SELECT name, licenses, availability, status FROM drivers")
                actual_headers = ['Driver Name', 'Licenses', 'Availability', 'Status']
                col_widths = [45, 75, 40, 30] 
                for row in cursor.fetchall():
                    actual_data.append([
                        remove_diacritics(str(row[0])), 
                        remove_diacritics(str(row[1])), 
                        remove_diacritics(str(row[2])), 
                        remove_diacritics(str(row[3]))
                    ])
                
            else:
                if 'Completed' in report['name']:
                    actual_headers = ['REQ ID', 'Client', 'Route (Pick -> Del)', 'Status']
                    col_widths = [40, 20, 85, 45]
                    cursor.execute("SELECT id, client, pickup, delivery, status FROM transport_requests WHERE status = 'Delivered'")
                    for row in cursor.fetchall():
                        pickup = remove_diacritics(str(row[2]))
                        delivery = remove_diacritics(str(row[3]))
                        actual_data.append([
                            remove_diacritics(str(row[0])), 
                            remove_diacritics(str(row[1])), 
                            f"{pickup} -> {delivery}", 
                            remove_diacritics(str(row[4]))
                        ])
                        
                elif 'Financial' in report['name']:
                    actual_headers = ['REQ ID', 'Client', 'Route', 'Status', 'Revenue']
                    col_widths = [35, 15, 75, 35, 30]
                    # Selectăm explicit coloana price_offer pe poziția 5
                    cursor.execute("SELECT id, client, pickup, delivery, status, price_offer FROM transport_requests WHERE status IN ('Paid', 'In Transit', 'Accepted', 'Delivered')")
                    for row in cursor.fetchall():
                        pickup = remove_diacritics(str(row[2]))
                        delivery = remove_diacritics(str(row[3]))
                        
                        # Formatăm prețul corect (evităm erori dacă e None sau text invalid)
                        raw_price = row[5]
                        try:
                            price_val = float(raw_price)
                            price = f"${price_val:.2f}"
                        except (ValueError, TypeError):
                            price = "$0.00"
                        
                        actual_data.append([
                            remove_diacritics(str(row[0])), 
                            remove_diacritics(str(row[1])), 
                            f"{pickup} -> {delivery}", 
                            remove_diacritics(str(row[4])),
                            price
                        ])
                else:
                    actual_headers = ['REQ ID', 'Client', 'Route', 'Status']
                    col_widths = [40, 20, 85, 45]
                    cursor.execute("SELECT id, client, pickup, delivery, status FROM transport_requests")
                    for row in cursor.fetchall():
                        pickup = remove_diacritics(str(row[2]))
                        delivery = remove_diacritics(str(row[3]))
                        actual_data.append([
                            remove_diacritics(str(row[0])), 
                            remove_diacritics(str(row[1])), 
                            f"{pickup} -> {delivery}", 
                            remove_diacritics(str(row[4]))
                        ])
                    
    except Exception as e:
        logging.error(f"Eroare extragere date SQL pt raport: {e}")
        actual_headers = ["System Error"]
        col_widths = [190]
        actual_data = [[f"Eroare la citirea bazei de date. (Detalii: {str(e)})"]]

    # --- LOGICA PDF ---
    if file_type == 'pdf':
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, txt="TRANSPORT COMPANY - OFFICIAL REPORT", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(50, 8, "Field", border=1, fill=True)
        pdf.cell(140, 8, "Details", border=1, ln=True, fill=True)
        
        pdf.set_font("Arial", '', 11)
        clean_title = clean_report_name.replace("Summary Summary", "Summary")
        
        meta_rows = [
            ("Report ID", report['id']),
            ("Report Name", clean_title),
            ("Category Type", report['type']),
            ("Generated By", remove_diacritics(report['generated_by'])),
            ("Generation Date", report['generated_date'])
        ]
        for label, value in meta_rows:
            pdf.cell(50, 8, label, border=1)
            pdf.cell(140, 8, str(value), border=1, ln=True)

        pdf.ln(10)

        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, txt="DETAILED ANALYTICS DATA", ln=True, align='L')
        pdf.ln(2)

        if actual_headers:
            pdf.set_font("Arial", 'B', 10)
            pdf.set_fill_color(0, 120, 212) 
            pdf.set_text_color(255, 255, 255)
            
            for i, h in enumerate(actual_headers):
                pdf.cell(col_widths[i], 8, str(h), border=1, fill=True, align='C')
            pdf.ln(8)

            pdf.set_font("Arial", '', 9)
            pdf.set_text_color(0, 0, 0)
            
            for row in actual_data:
                render_pdf_row(pdf, row, col_widths)

        response = make_response(pdf.output(dest='S').encode('latin-1'))
        response.headers["Content-Disposition"] = f"attachment; filename={filename}.pdf"
        response.headers["Content-type"] = "application/pdf"
        return response

    # --- LOGICA CSV ---
    elif file_type == 'csv':
        output = io.StringIO()
        # Folosim virgula standard, dar FORȚĂM ghilimelele pentru fiecare celulă (QUOTE_ALL)
        # Asta împiedică Excel/Numbers să mai taie textul când întâlnește spații.
        writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_ALL)
        
        writer.writerow(['--- REPORT METADATA ---'])
        writer.writerow(['Report ID', 'Name', 'Type', 'Generated By', 'Date'])
        writer.writerow([report['id'], report['name'].replace("Summary Summary", "Summary"), report['type'], report['generated_by'], report['generated_date']])
        
        writer.writerow([]) 
        writer.writerow(['--- DETAILED DATA ---'])
        
        if actual_headers:
            writer.writerow(actual_headers)
            writer.writerows(actual_data)
        
        # utf-8-sig previne apariția caracterelor ciudate în loc de diacritice
        csv_data = output.getvalue().encode('utf-8-sig')
        
        response = make_response(csv_data)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}.csv"
        response.headers["Content-type"] = "text/csv; charset=utf-8-sig"
        return response

    # --- LOGICA TXT ---
    elif file_type == 'txt':
        clean_title = report['name'].replace("Summary Summary", "Summary")
        content = f"=== REPORT {report_id} ===\n"
        content += f"Name: {clean_title}\nType: {report['type']}\nUser: {report['generated_by']}\nDate: {report['generated_date']}\n\n"
        
        content += "=== DETAILED DATA ===\n"
        if actual_headers:
            content += " | ".join(actual_headers) + "\n"
            content += "-" * 60 + "\n"
            for row in actual_data:
                content += " | ".join(row) + "\n"
        
        response = make_response(content)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}.txt"
        response.headers["Content-type"] = "text/plain"
        return response

    return redirect(url_for('report_routes.reports_management'))