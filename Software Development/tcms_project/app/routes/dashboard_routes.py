import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.controllers.dashboard_controller import DashboardController
from app.models.notification_model import NotificationModel 
from app.models.request_model import RequestModel # 🔴 NOU: Aducem modelul de cereri

dashboard_bp = Blueprint('dashboard', __name__)
dashboard_logic = DashboardController()
notif_db = NotificationModel() 
req_model = RequestModel() # 🔴 NOU: Inițializăm modelul

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
        return redirect(url_for('driver.portal')) 
        
    elif user_role == 'Staff':
        try:
            view_data = dashboard_logic.load_staff_dashboard_data()
            
            # 🔴 NOU: Atașăm istoricul de negocieri pentru fiecare cursă!
            if 'recent_requests' in view_data:
                updated_requests = []
                for req in view_data['recent_requests']:
                    req_dict = dict(req) # Convertim rândul din BD în dicționar
                    req_dict['messages'] = req_model.get_negotiation_messages(req_dict['id'])
                    updated_requests.append(req_dict)
                view_data['recent_requests'] = updated_requests
                
            notifications = notif_db.get_unread_notifications(username, user_role)
            
            return render_template(
                'staff/portal.html', 
                data=view_data, 
                role=user_role, 
                username=username,
                notifications=notifications, 
                unread_count=len(notifications) 
            )
        except Exception as routing_error:
            logging.error(f"Staff routing error: {routing_error}")
            flash(f"Dashboard Error (Staff): {routing_error}", "danger")
            return redirect(url_for('auth.login'))
            
    else: # Pentru Administrator
        try:
            view_data = dashboard_logic.load_dashboard_data()
            
            # 🔴 NOU: Atașăm istoricul de negocieri pentru fiecare cursă!
            if 'recent_requests' in view_data:
                updated_requests = []
                for req in view_data['recent_requests']:
                    req_dict = dict(req) # Convertim rândul din BD în dicționar
                    req_dict['messages'] = req_model.get_negotiation_messages(req_dict['id'])
                    updated_requests.append(req_dict)
                view_data['recent_requests'] = updated_requests
                
            notifications = notif_db.get_unread_notifications(username, user_role)
            
            return render_template(
                'admin/dashboard.html', 
                data=view_data, 
                role=user_role, 
                username=username,
                notifications=notifications, 
                unread_count=len(notifications) 
            )
        except Exception as routing_error:
            logging.error(f"Admin routing error: {routing_error}")
            flash(f"Dashboard Error (Admin): {routing_error}", "danger")
            return redirect(url_for('auth.login'))

@dashboard_bp.route('/dashboard/schedule')
def driver_schedule() -> str:
    """Renders the Schedule Calendar for Drivers and Jobs."""
    if 'user_id' not in session or session.get('role') not in ['Administrator', 'Staff']:
        flash("Access denied. Only Staff and Admins can view the schedule.", "danger")
        return redirect(url_for('auth.login'))

    user_role = session.get('role')
    username = session.get('username')
    notifications = notif_db.get_unread_notifications(username, user_role)
    
    # Tragem evenimentele direct din model
    calendar_events = dashboard_logic.model.get_driver_schedules()
    
    return render_template(
        'admin/driver_schedule.html',
        role=user_role,
        username=username,
        notifications=notifications,
        unread_count=len(notifications),
        events=calendar_events # Trimitem datele calendarului catre HTML
    )