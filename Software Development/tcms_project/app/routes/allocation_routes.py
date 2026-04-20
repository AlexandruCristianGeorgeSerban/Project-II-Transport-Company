import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.controllers.allocation_controller import AllocationController
from app.models.notification_model import NotificationModel

allocation_bp = Blueprint('allocation', __name__)
allocation_logic = AllocationController()

@allocation_bp.route('/allocation', methods=['GET'])
def allocation_management() -> str:
    """Renders the Allocation Module page."""
    if 'user_id' not in session:
        flash("Please log in.", "danger")
        return redirect(url_for('auth.login'))
    
    view_data = allocation_logic.load_allocation_data()
    role = session.get('role', 'Staff')
    
    return render_template('staff/allocation.html', data=view_data, role=role)

@allocation_bp.route('/allocation/confirm', methods=['POST'])
def confirm_allocation() -> str:
    """Handles the allocation form submission."""
    req_id = request.form.get('request_id')
    veh_id = request.form.get('vehicle_id')
    drv_id = request.form.get('driver_id')
    
    response = allocation_logic.process_allocation(req_id, veh_id, drv_id)
    
    if response.get("success") is True:
        notif_db = NotificationModel()
        notif_db.add_notification('All', f"Job-ul {req_id} a fost alocat pe mașina {veh_id}.")
        flash(response.get("message"), "success")
    else:
        flash(response.get("message"), "danger")
        
    return redirect(url_for('allocation.allocation_management'))