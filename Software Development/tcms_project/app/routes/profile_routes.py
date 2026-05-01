from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.controllers.profile_controller import ProfileController

profile_bp = Blueprint('profile', __name__)
profile_logic = ProfileController()

@profile_bp.route('/profile', methods=['GET'])
def view_profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_data = profile_logic.get_user_profile(session['user_id'])
    return render_template('profile.html', user=user_data)

@profile_bp.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    profile_pic = request.files.get('profile_picture')
        
    result = profile_logic.update_profile(
        session['user_id'],
        request.form.get('username'),
        request.form.get('email'),
        request.form.get('first_name'),
        request.form.get('last_name'),
        request.form.get('phone'),
        request.form.get('address'),
        profile_pic
    )
    
    if result['success']:
        flash(result['message'], "success")
        session['username'] = result.get('new_username', session.get('username'))
        if result.get('new_pic'):
            session['profile_picture'] = result['new_pic']
    else:
        flash(result['message'], "danger")
        
    return redirect(url_for('profile.view_profile'))

@profile_bp.route('/profile/password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    result = profile_logic.change_password(
        session['user_id'],
        request.form.get('current_password'),
        request.form.get('new_password')
    )
    flash(result['message'], "success" if result['success'] else "danger")
    return redirect(url_for('profile.view_profile'))

@profile_bp.route('/profile/delete', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    result = profile_logic.delete_account(session['user_id'])
    if result['success']:
        session.clear()
        flash("Your account has been deleted.", "info")
        return redirect(url_for('auth.login'))
    else:
        flash(result['message'], "danger")
        return redirect(url_for('profile.view_profile'))

@profile_bp.route('/profile/back')
def back_to_dashboard():
    role = session.get('role')
    if role == 'Customer': 
        return redirect(url_for('customer.portal'))
    elif role == 'Driver': 
        return redirect(url_for('driver.portal'))
    else: 
        return redirect(url_for('dashboard.main_dashboard'))