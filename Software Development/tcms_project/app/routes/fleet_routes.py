import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.controllers.fleet_controller import FleetController

fleet_bp = Blueprint('fleet', __name__)
fleet_logic = FleetController()

@fleet_bp.route('/fleet', methods=['GET'])
def fleet_management() -> str:
    """Renders the main Fleet Management page."""
    if 'user_id' not in session:
        flash("Please log in to access Fleet Management.", "danger")
        return redirect(url_for('auth.login'))
    
    try:
        view_data = fleet_logic.load_fleet_data()
        user_role = session.get('role', 'Staff')
        username = session.get('username', 'User')
        
        return render_template(
            'admin/fleet.html', 
            data=view_data, 
            role=user_role, 
            username=username
        )
    except Exception as routing_error:
        logging.error(f"Fleet routing error: {routing_error}")
        flash("An error occurred while loading the fleet module.", "danger")
        return redirect(url_for('dashboard.main_dashboard'))

@fleet_bp.route('/fleet/add', methods=['POST'])
def add_vehicle() -> str:
    v_id = request.form.get('vehicle_id')
    plate = request.form.get('plate_number')
    v_type = request.form.get('type')
    capacity = float(request.form.get('capacity', 0.0))
    cap_unit = request.form.get('capacity_unit')
    status = request.form.get('status')

    final_capacity = capacity * 1000 if cap_unit == 'tons' else capacity
    
    modified_by = session.get('username', 'System')

    response = fleet_logic.add_new_vehicle(v_id, plate, v_type, final_capacity, status, modified_by)
    flash(response.get("message"), "success" if response.get("success") else "danger")
    return redirect(url_for('fleet.fleet_management'))

@fleet_bp.route('/fleet/edit', methods=['POST'])
def edit_vehicle() -> str:
    v_id = request.form.get('edit_vehicle_id')
    plate = request.form.get('edit_plate_number')
    v_type = request.form.get('edit_type')
    capacity = float(request.form.get('edit_capacity', 0.0))
    cap_unit = request.form.get('edit_capacity_unit')
    status = request.form.get('edit_status')

    final_capacity = capacity * 1000 if cap_unit == 'tons' else capacity
    
    modified_by = session.get('username', 'System')

    response = fleet_logic.modify_vehicle(v_id, plate, v_type, final_capacity, status, modified_by)
    flash(response.get("message"), "success" if response.get("success") else "danger")
    return redirect(url_for('fleet.fleet_management'))

@fleet_bp.route('/fleet/delete/<vehicle_id>', methods=['POST'])
def delete_vehicle(vehicle_id: str) -> str:
    modified_by = session.get('username', 'System')
    
    response = fleet_logic.remove_vehicle(vehicle_id, modified_by)
    flash(response.get("message"), "success" if response.get("success") else "danger")
    return redirect(url_for('fleet.fleet_management'))