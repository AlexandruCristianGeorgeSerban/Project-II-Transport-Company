import logging
from flask import Blueprint, redirect, request, session, url_for
from app.models.notification_model import NotificationModel

notification_bp = Blueprint('notifications', __name__)
notif_db = NotificationModel()

@notification_bp.route('/notifications/read/<int:notif_id>', methods=['GET', 'POST'])
def read_notification(notif_id):
    """Marchează notificarea ca citită și te întoarce pe pagina unde erai sau pe target_url."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # 1. Extragem link-ul
    target_url = notif_db.get_notification_url(notif_id)
        
    # 2. Marcăm ca citită direct în Baza de date (blindat)
    notif_db.mark_as_read(notif_id)
    
    # 3. Mergem acolo unde ne cere link-ul
    if target_url and str(target_url).strip() != "":
        return redirect(target_url)
    
    # Dacă nu are link, ne întoarcem unde eram
    return redirect(request.referrer or url_for('dashboard.main_dashboard'))