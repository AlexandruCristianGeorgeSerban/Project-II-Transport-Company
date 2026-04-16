import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash
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
    
    # Customer redirect
    if user_role == 'Customer':
        return redirect(url_for('customer.portal'))
    
    # Pentru Admin sau Staff: Incarcam datele doar pentru citire (Read-Only)
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