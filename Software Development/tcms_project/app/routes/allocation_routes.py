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

    if not driver_data or not vehicle_data:
         flash("Error: Could not retrieve driver or vehicle details for validation.", "danger")
         return redirect(url_for('allocation.allocation_management'))

    if vehicle_data.get('status') != 'Available':
        flash(f"Error: Vehiculul {vehicle_data['plate_number']} a fost deja preluat sau e în mentenanță!", "danger")
        return redirect(url_for('allocation.allocation_management'))
        
    if driver_data.get('availability') != 'Available':
        flash(f"Error: Șoferul {driver_data['name']} nu mai este disponibil momentan!", "danger")
        return redirect(url_for('allocation.allocation_management'))

    try:
        with sqlite3.connect("instance/database.sqlite") as conn:
            conn.row_factory = sqlite3.Row
            req_data = conn.execute("SELECT weight FROM transport_requests WHERE id = ?", (req_id,)).fetchone()
            
            if req_data:
                cargo_weight = float(req_data['weight'])
                vehicle_capacity = float(vehicle_data.get('capacity', 0))
                
                if vehicle_capacity < cargo_weight:
                    flash(f"Eroare Matematică: Vehiculul {vehicle_data['plate_number']} (Capacitate: {vehicle_capacity}kg) nu poate duce marfa de {cargo_weight}kg!", "danger")
                    return redirect(url_for('allocation.allocation_management'))
    except Exception as e:
        logging.error(f"Eroare la verificarea capacitatii: {e}")

    is_compatible = check_license_compatibility(driver_data['licenses'], vehicle_data['type'])
    if not is_compatible:
        flash(f"Error Legal: Șoferul {driver_data['name']} (Licențe: {driver_data['licenses']}) NU are voie să conducă {vehicle_data['type']}!", "danger")
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
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    role = session.get('role')
    
    # 🔴 SOLUȚIA PENTRU CONFLICT:
    # Dacă e șofer, îl aruncăm direct în portalul lui! 
    # Nu are ce căuta pe tabelul de Staff.
    if role == 'Driver':
        return redirect(url_for('driver.portal'))
        
    if role not in ['Administrator', 'Staff']:
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.main_dashboard'))
        
    view_data = allocation_logic.load_active_jobs()
    return render_template('staff/active_jobs.html', data=view_data, role=role)

@allocation_bp.route('/active_jobs/deliver/<req_id>', methods=['POST'])
def deliver_job(req_id: str):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    role = session.get('role')
    if role not in ['Administrator', 'Staff', 'Driver']:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('auth.login'))
        
    response = allocation_logic.complete_active_job(req_id)
    if response.get("success") is True: flash(response.get("message"), "success")
    else: flash(response.get("message"), "danger")
        
    return redirect(url_for('allocation.active_jobs'))

@allocation_bp.route('/api/locations')
def api_locations():
    try:
        with sqlite3.connect("instance/database.sqlite") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, current_lat, current_lng, pickup, delivery FROM transport_requests WHERE status = 'In Transit'")
            jobs = cursor.fetchall()
            locations = [{"id": job['id'], "lat": job['current_lat'], "lng": job['current_lng'], "pickup": job['pickup'], "delivery": job['delivery']} for job in jobs]
            return jsonify(locations)
    except Exception as e:
        logging.error(f"Error fetching locations API: {e}")
        return jsonify([])

@allocation_bp.route('/api/network_data')
def network_data():
    if 'user_id' not in session: return jsonify({"nodes": [], "edges": []})
        
    try:
        with sqlite3.connect("instance/database.sqlite") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name FROM drivers WHERE availability != 'On Leave'")
            drivers = cursor.fetchall()
            
            cursor.execute("SELECT id, plate_number FROM vehicles")
            vehicles = cursor.fetchall()
            
            cursor.execute("SELECT id, vehicle_id, driver_id, client FROM transport_requests WHERE status IN ('In Transit', 'Accepted')")
            allocations = cursor.fetchall()
            
            nodes = []
            edges = []
            added_clients = set()
            
            for d in drivers:
                nodes.append({"id": f"D_{d['id']}", "label": f"👨‍✈️ {d['name']}\n(Driver)", "group": "driver"})
                
            for v in vehicles:
                nodes.append({"id": f"V_{v['id']}", "label": f"🚛 {v['plate_number']}\n(Vehicle)", "group": "vehicle"})
                
            for req in allocations:
                req_id = req['id']
                v_id = req['vehicle_id']
                d_id = req['driver_id']
                client_name = req['client']
                
                client_node_id = f"C_{client_name}"
                if client_node_id not in added_clients:
                    nodes.append({"id": client_node_id, "label": f"🏢 {client_name}\n(Customer)", "group": "customer"})
                    added_clients.add(client_node_id)
                
                is_admin = len(req_id) < 10
                req_group = "request_admin" if is_admin else "request"
                req_icon = "🛠️" if is_admin else "📦"
                
                nodes.append({"id": f"R_{req_id}", "label": f"{req_icon} {req_id}\n(Order)", "group": req_group})
                
                edges.append({"from": client_node_id, "to": f"R_{req_id}", "label": "Orders", "arrows": "to"})
                
                if v_id:
                    edges.append({"from": f"R_{req_id}", "to": f"V_{v_id}", "label": "Assigned To", "arrows": "to"})
                if d_id and v_id:
                    edges.append({"from": f"V_{v_id}", "to": f"D_{d_id}", "label": "Driven By", "arrows": "to"})
                    
            return jsonify({"nodes": nodes, "edges": edges})
            
    except Exception as e:
        logging.error(f"Error generating network data: {e}")
        return jsonify({"nodes": [], "edges": []})