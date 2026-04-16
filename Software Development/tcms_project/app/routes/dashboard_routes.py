import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.controllers.dashboard_controller import DashboardController

dashboard_bp = Blueprint('dashboard', __name__)
dashboard_logic = DashboardController()

@dashboard_bp.route('/dashboard')
def main_dashboard() -> str:
    """Renders the main dashboard page with READ data or redirects based on user role."""
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "danger")
        return redirect(url_for('auth.login'))
    
    user_role = session.get('role', 'Staff')
    
    # Customer:
    if user_role == 'Customer':
        return redirect(url_for('customer.portal'))
    
    # Daca e Admin sau Staff:
    try:
        view_data = dashboard_logic.load_dashboard_data()
        return render_template(
            'admin/dashboard.html', 
            data=view_data, 
            role=user_role, 
            username=session.get('username', 'User')
        )
    except Exception as routing_error:
        logging.error(f"Dashboard routing error: {routing_error}")
        flash("An error occurred while loading the dashboard.", "danger")
        return redirect(url_for('auth.login'))

@dashboard_bp.route('/dashboard/add', methods=['POST'])
def add_request() -> str:
    """Endpoint to CREATE a new request."""
    client = request.form.get('client', '')
    pickup = request.form.get('pickup', '')
    delivery = request.form.get('delivery', '')
    status = request.form.get('status', 'Pending')
    
    response = dashboard_logic.add_new_request(client, pickup, delivery, status)
    
    if response.get("success") is True:
        flash(response.get("message"), "success")
    else:
        flash(response.get("message"), "danger")
        
    return redirect(url_for('dashboard.main_dashboard'))

@dashboard_bp.route('/dashboard/delete/<int:request_id>', methods=['POST'])
def delete_request(request_id: int) -> str:
    """Endpoint to DELETE a request."""
    response = dashboard_logic.remove_request(request_id)
    
    if response.get("success") is True:
        flash(response.get("message"), "success")
    else:
        flash(response.get("message"), "danger")
        
    return redirect(url_for('dashboard.main_dashboard'))

@dashboard_bp.route('/dashboard/edit/<int:request_id>', methods=['POST'])
def edit_request(request_id: int) -> str:
    """Endpoint to UPDATE an existing request."""
    client = request.form.get('client', '')
    pickup = request.form.get('pickup', '')
    delivery = request.form.get('delivery', '')
    status = request.form.get('status', 'Pending')
    
    response = dashboard_logic.modify_request(request_id, client, pickup, delivery, status)
    
    if response.get("success") is True:
        flash(response.get("message"), "success")
    else:
        flash(response.get("message"), "danger")
        
    return redirect(url_for('dashboard.main_dashboard'))