from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.controllers.driver_portal_controller import DriverPortalController

driver_portal_bp = Blueprint('driver_portal', __name__)
portal_logic = DriverPortalController()

@driver_portal_bp.route('/driver/dashboard')
def portal():
    if session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))
    
    username = session.get('username')
    jobs = portal_logic.get_driver_jobs(username)
    
    driver_status = 'Available'
    for job in jobs:
        if job['status'] == 'In Transit':
            driver_status = 'Busy'
            break
            
    unread_count = 0
    notifications = []
    
    return render_template('driver/portal.html', 
                           username=username, 
                           jobs=jobs, 
                           driver_status=driver_status,
                           unread_count=unread_count,
                           notifications=notifications)

@driver_portal_bp.route('/driver/history')
def history():
    if session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))
    
    username = session.get('username')
    jobs = portal_logic.get_driver_jobs(username)
    
    unread_count = 0
    notifications = []
    
    return render_template('driver/history.html', 
                           username=username, 
                           jobs=jobs, 
                           driver_status='Available',
                           unread_count=unread_count,
                           notifications=notifications)

@driver_portal_bp.route('/driver/update_status/<req_id>/<new_status>', methods=['POST'])
def update_status(req_id, new_status):
    if session.get('role') != 'Driver':
        return redirect(url_for('auth.login'))
        
    username = session.get('username')
    result = portal_logic.update_status(req_id, new_status, username)
    
    if result['success']:
        flash(result['message'], "success")
    else:
        flash(result['message'], "danger")
        
    return redirect(url_for('driver_portal.portal'))