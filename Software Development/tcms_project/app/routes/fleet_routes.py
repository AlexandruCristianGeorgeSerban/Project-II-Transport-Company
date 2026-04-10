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
    """Handles the form submission to add a new vehicle."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    v_id = request.form.get('vehicle_id')
    plate = request.form.get('plate_number')
    v_type = request.form.get('type')
    capacity_str = request.form.get('capacity')
    status = request.form.get('status')

    try:
        capacity = int(capacity_str)
        response = fleet_logic.add_new_vehicle(v_id, plate, v_type, capacity, status)

        if response.get("success") is True:
            flash(response.get("message"), "success")
        else:
            flash(response.get("message"), "danger")

    except ValueError as val_error:
        logging.error(f"Capacity casting error: {val_error}")
        flash("Capacity must be a valid number.", "danger")

    return redirect(url_for('fleet.fleet_management'))

@fleet_bp.route('/fleet/delete/<vehicle_id>', methods=['POST'])
def delete_vehicle(vehicle_id: str) -> str:
    """Handles the deletion of a specific vehicle."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    response = fleet_logic.remove_vehicle(vehicle_id)

    if response.get("success") is True:
        flash(response.get("message"), "success")
    else:
        flash(response.get("message"), "danger")

    return redirect(url_for('fleet.fleet_management'))

@fleet_bp.route('/fleet/edit', methods=['POST'])
def edit_vehicle() -> str:
    """Handles the form submission to edit an existing vehicle."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    v_id = request.form.get('edit_vehicle_id')
    plate = request.form.get('edit_plate_number')
    v_type = request.form.get('edit_type')
    capacity_str = request.form.get('edit_capacity')
    status = request.form.get('edit_status')

    try:
        capacity = int(capacity_str)
        response = fleet_logic.modify_vehicle(v_id, plate, v_type, capacity, status)

        if response.get("success") is True:
            flash(response.get("message"), "success")
        else:
            flash(response.get("message"), "danger")

    except ValueError as val_error:
        logging.error(f"Capacity casting error: {val_error}")
        flash("Capacity must be a valid number.", "danger")

    return redirect(url_for('fleet.fleet_management'))