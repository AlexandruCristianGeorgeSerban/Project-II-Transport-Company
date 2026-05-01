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
    
    role = session.get('role')
    # Protejăm ruta: doar Admin și Staff pot face alocări
    if role not in ['Administrator', 'Staff']:
        flash("Access denied. You do not have permission to view allocations.", "danger")
        return redirect(url_for('dashboard.main_dashboard'))
    
    view_data = allocation_logic.load_allocation_data()
    return render_template('staff/allocation.html', data=view_data, role=role)

@allocation_bp.route('/allocation/confirm', methods=['POST'])
def confirm_allocation() -> str:
    """Handles the allocation form submission."""
    # Protecție la nivel de backend pentru POST
    if 'user_id' not in session or session.get('role') not in ['Administrator', 'Staff']:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('auth.login'))

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

@allocation_bp.route('/active_jobs', methods=['GET'])
def active_jobs() -> str:
    """Afișează ecranul cu cursele aflate pe traseu."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    role = session.get('role')
    
    # AICI ESTE SECRETUL: Permitem și rolului 'Driver' să acceseze această pagină
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
    
    # Oferim permisiunea șoferului să execute această acțiune
    if role not in ['Administrator', 'Staff', 'Driver']:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('auth.login'))
        
    response = allocation_logic.complete_active_job(req_id)
    
    if response.get("success") is True:
        flash(response.get("message"), "success")
    else:
        flash(response.get("message"), "danger")
        
    return redirect(url_for('allocation.active_jobs'))