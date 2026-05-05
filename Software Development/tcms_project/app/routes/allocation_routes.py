import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from app.controllers.allocation_controller import AllocationController, check_license_compatibility
from app.models.notification_model import NotificationModel
from app.models.driver_model import DriverModel
from app.models.fleet_model import FleetModel
import sqlite3

allocation_bp = Blueprint('allocation', __name__)
allocation_logic = AllocationController()

@allocation_bp.route('/allocation', methods=['GET'])
def allocation_management() -> str:
    """Renders the Allocation Module page."""
    if 'user_id' not in session:
        flash("Please log in.", "danger")
        return redirect(url_for('auth.login'))
    
    role = session.get('role')
    if role not in ['Administrator', 'Staff']:
        flash("Access denied. You do not have permission to view allocations.", "danger")
        return redirect(url_for('dashboard.main_dashboard'))
    
    view_data = allocation_logic.load_allocation_data()
    return render_template('staff/allocation.html', data=view_data, role=role)

@allocation_bp.route('/allocation/confirm', methods=['POST'])
def confirm_allocation() -> str:
    """Handles the allocation form submission, including license and capacity validation."""
    if 'user_id' not in session or session.get('role') not in ['Administrator', 'Staff']:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('auth.login'))

    req_id = request.form.get('request_id')
    veh_id = request.form.get('vehicle_id')
    drv_id = request.form.get('driver_id')
    
    
    staff_username = session.get('username', 'Unknown')
    
    driver_db = DriverModel()
    fleet_db = FleetModel()
    
    driver_data = driver_db.get_driver_by_id(drv_id)
    vehicle_data = fleet_db.get_vehicle_by_id(veh_id)

    
    try:
        with sqlite3.connect("instance/database.sqlite") as conn:
            conn.row_factory = sqlite3.Row
            req_data = conn.execute("SELECT weight FROM transport_requests WHERE id = ?", (req_id,)).fetchone()
            
            if req_data and vehicle_data:
                cargo_weight = float(req_data['weight'])
                vehicle_capacity = float(vehicle_data.get('capacity', 0))
                
                
                if vehicle_capacity < cargo_weight:
                    flash(f"Eroare: Vehiculul {vehicle_data['plate_number']} (Capacitate: {vehicle_capacity}kg) nu poate transporta marfa de {cargo_weight}kg!", "danger")
                    return redirect(url_for('allocation.allocation_management'))
    except Exception as e:
        logging.error(f"Eroare la verificarea capacitatii: {e}")

    
    if driver_data and vehicle_data:
        is_compatible = check_license_compatibility(driver_data['licenses'], vehicle_data['type'])

        if not is_compatible:
            flash(f"Error: Driver {driver_data['name']} (Licenses: {driver_data['licenses']}) cannot drive a {vehicle_data['type']}!", "danger")
            return redirect(url_for('allocation.allocation_management'))
    else:
         flash("Error: Could not retrieve driver or vehicle details for validation.", "danger")
         return redirect(url_for('allocation.allocation_management'))

    
    response = allocation_logic.process_allocation(req_id, veh_id, drv_id, staff_username)
    
    if response.get("success") is True:
        notif_db = NotificationModel()
        notif_db.add_notification('All', f"Job-ul {req_id} a fost alocat pe mașina {veh_id}.")
        flash(response.get("message"), "success")
    else:
        flash(response.get("message"), "danger")
        
    return redirect(url_for('allocation.allocation_management'))

@allocation_bp.route('/active_jobs', methods=['GET'])
def active_jobs() -> str:
    """Afișează ecranul cu cursele aflate pe traseu."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    role = session.get('role')
    if role not in ['Administrator', 'Staff', 'Driver']:
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.main_dashboard'))
        
    view_data = allocation_logic.load_active_jobs()
    return render_template('staff/active_jobs.html', data=view_data, role=role)

@allocation_bp.route('/active_jobs/deliver/<req_id>', methods=['POST'])
def deliver_job(req_id: str):
    """Procesează butonul de 'Mark as Delivered'."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    role = session.get('role')
    if role not in ['Administrator', 'Staff', 'Driver']:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('auth.login'))
        
    response = allocation_logic.complete_active_job(req_id)
    
    if response.get("success") is True:
        flash(response.get("message"), "success")
    else:
        flash(response.get("message"), "danger")
        
    return redirect(url_for('allocation.active_jobs'))

@allocation_bp.route('/api/locations')
def api_locations():
    """Returnează coordonatele tuturor curselor In Transit, citind direct din DB."""
    try:
        with sqlite3.connect("instance/database.sqlite") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, current_lat, current_lng FROM transport_requests WHERE status = 'In Transit'")
            jobs = cursor.fetchall()
            
            locations = []
            for job in jobs:
                locations.append({
                    "id": job['id'],
                    "lat": job['current_lat'],
                    "lng": job['current_lng']
                })
            return jsonify(locations)
    except Exception as e:
        logging.error(f"Error fetching locations API: {e}")
        return jsonify([])