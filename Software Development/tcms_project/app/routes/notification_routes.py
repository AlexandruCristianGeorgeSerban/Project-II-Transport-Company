import logging
from flask import Blueprint, redirect, request, session, flash, url_for
from app.controllers.notification_controller import NotificationController

notification_bp = Blueprint('notifications', __name__)
notif_logic = NotificationController()

@notification_bp.route('/notifications/read/<int:notif_id>', methods=['GET', 'POST'])
def read_notification(notif_id):
    """Marchează notificarea ca citită și te întoarce pe pagina unde erai."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    notif_logic.mark_notification_as_read(notif_id)
    
    return redirect(request.referrer or url_for('dashboard.main_dashboard'))