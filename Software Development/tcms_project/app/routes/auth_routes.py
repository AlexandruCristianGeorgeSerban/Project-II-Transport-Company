import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.controllers.auth_controller import AuthController

auth_bp = Blueprint('auth', __name__)
auth_logic = AuthController()

@auth_bp.route('/', methods=['GET', 'POST'])
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
            
            # AICI E MODIFICAREA: Trimitem toti utilizatorii logati catre noul dashboard
            return redirect(url_for('dashboard.main_dashboard'))
        else:
            flash(auth_result.get("message"), "danger")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register() -> str:
    """Renders the registration page and handles new account creation."""
    if request.method == 'POST':
        reg_username = request.form.get('username')
        reg_password = request.form.get('password')
        reg_dob = request.form.get('date_of_birth')
        
        reg_result = auth_logic.register_customer(reg_username, reg_password, reg_dob)
        
        if reg_result.get("success") is True:
            flash(reg_result.get("message"), "success")
            return redirect(url_for('auth.login'))
        else:
            flash(reg_result.get("message"), "danger")
            return render_template('auth/register.html')
    else:
        return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout() -> str:
    """Destroys the user session and redirects to login."""
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('auth.login'))