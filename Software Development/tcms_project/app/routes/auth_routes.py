import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask import request, redirect, url_for, flash, render_template
from app.controllers.auth_controller import AuthController

auth_bp = Blueprint('auth', __name__)
auth_logic = AuthController()

# 1. RUTA PENTRU GUEST PAGE
@auth_bp.route('/', methods=['GET'])
def guest():
    """Renders the Guest landing page without auto-redirecting."""
    return render_template('guest/home.html')

# 2. RUTA PENTRU LOGIN
@auth_bp.route('/login', methods=['GET', 'POST'])
def login() -> str:
    """Renders the login page and handles authentication requests."""
    if request.method == 'POST':
        form_username = request.form.get('username')
        form_password = request.form.get('password')
        
        auth_result = auth_logic.authenticate_user(form_username, form_password)
        
        if auth_result.get("success") is True:
            session['user_id'] = auth_result.get("user_id")
            session['role'] = auth_result.get("role")
            session['username'] = auth_result.get("username")
            
            
            if "profile_picture" in auth_result and auth_result["profile_picture"]:
                session['profile_picture'] = auth_result["profile_picture"]
            else:
                
                session.pop('profile_picture', None)
            if session['role'] == 'Customer':
                return redirect(url_for('customer.portal'))
            elif session['role'] == 'Driver':
                
                return redirect(url_for('driver.portal'))
            else:
                return redirect(url_for('dashboard.main_dashboard'))
        else:
            flash(auth_result.get("message"), "danger")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')

# 3. RUTA PENTRU REGISTER
@auth_bp.route('/register', methods=['GET', 'POST'])
def register() -> str:
    """Renders the registration page and handles new account creation."""
    if request.method == 'POST':
        reg_username = request.form.get('username')
        reg_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        reg_first_name = request.form.get('first_name')
        reg_last_name = request.form.get('last_name')
        reg_email = request.form.get('email')
        reg_phone = request.form.get('phone_number')
        reg_dob = request.form.get('date_of_birth')

        # Verificăm parolele
        if reg_password != confirm_password:
             flash("Passwords do not match!", "danger")
             return render_template('auth/register.html')

        # Trimitem la controller
        reg_result = auth_logic.register_customer(
            username=reg_username, 
            password=reg_password, 
            first_name=reg_first_name, 
            last_name=reg_last_name, 
            email=reg_email, 
            phone_number=reg_phone,
            date_of_birth=reg_dob
        )
        
        if reg_result.get("success") is True:
            flash(reg_result.get("message"), "success")
            return redirect(url_for('auth.login'))
        else:
            flash(reg_result.get("message"), "danger")
            return render_template('auth/register.html')
    else:
        return render_template('auth/register.html')

# 4. RUTA PENTRU LOGOUT
@auth_bp.route('/logout')
def logout() -> str:
    """Destroys the user session and redirects to login."""
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('auth.login'))