import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.controllers.dashboard_controller import DashboardController
from app.models.notification_model import NotificationModel # ADAUGAT: Importăm modelul de notificări

dashboard_bp = Blueprint('dashboard', __name__)
dashboard_logic = DashboardController()
notif_db = NotificationModel() # ADAUGAT: Inițializăm modelul

@dashboard_bp.route('/dashboard')
def main_dashboard() -> str:
    """Renders the main dashboard page or redirects based on user role."""
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "danger")
        return redirect(url_for('auth.login'))
    
    user_role = session.get('role', 'Staff')
    username = session.get('username', 'User')
    
    if user_role == 'Customer':
        return redirect(url_for('customer.portal'))
    elif user_role == 'Driver':
        return redirect(url_for('driver.portal')) # Asigură-te că endpoint-ul e corect (ex: 'driver.portal')
        
    elif user_role == 'Staff':
        try:
            view_data = dashboard_logic.load_staff_dashboard_data()
            # Preluăm notificările pentru Staff
            notifications = notif_db.get_unread_notifications(user_role)
            
            return render_template(
                'staff/portal.html', 
                data=view_data, 
                role=user_role, 
                username=username,
                notifications=notifications, # ADAUGAT: Trimitem notificările
                unread_count=len(notifications) # ADAUGAT: Trimitem numărul lor
            )
        except Exception as routing_error:
            logging.error(f"Staff routing error: {routing_error}")
            flash("An error occurred while loading the staff portal.", "danger")
            return redirect(url_for('auth.login'))
            
    else: # Pentru Administrator
        try:
            view_data = dashboard_logic.load_dashboard_data()
            # Preluăm notificările pentru Administrator
            notifications = notif_db.get_unread_notifications(user_role)
            
            return render_template(
                'admin/dashboard.html', 
                data=view_data, 
                role=user_role, 
                username=username,
                notifications=notifications, # ADAUGAT: Trimitem notificările
                unread_count=len(notifications) # ADAUGAT: Trimitem numărul lor
            )
        except Exception as routing_error:
            logging.error(f"Admin routing error: {routing_error}")
            flash("An error occurred while loading the dashboard.", "danger")
            return redirect(url_for('auth.login'))