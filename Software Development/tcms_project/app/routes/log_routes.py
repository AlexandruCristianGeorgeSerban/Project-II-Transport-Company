from flask import Blueprint, render_template, session, redirect, url_for
from app.controllers.log_controller import LogController

log_bp = Blueprint('logs', __name__)
log_logic = LogController()

@log_bp.route('/system_logs')
def view_logs():
    # Doar Adminul și Staff-ul au voie să vadă logurile sistemului
    if 'user_id' not in session or session.get('role') not in ['Administrator', 'Staff']:
        return redirect(url_for('auth.login'))

    logs_data = log_logic.get_logs_data()
    return render_template('admin/system_logs.html', logs=logs_data)