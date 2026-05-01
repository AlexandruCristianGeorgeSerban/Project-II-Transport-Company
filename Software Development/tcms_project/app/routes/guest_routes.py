from flask import Blueprint, render_template, redirect, url_for, session

guest_bp = Blueprint('guest', __name__)

@guest_bp.route('/')
def home():
    """Renders the landing page for guests with information and tutorial link."""
    # If a user is already logged in, redirect them to their respective dashboard
    if 'user_id' in session:
        role = session.get('role')
        if role == 'Customer':
            return redirect(url_for('customer.portal'))
        elif role in ['Staff', 'Administrator']:
            return redirect(url_for('dashboard.main_dashboard'))
            
    return render_template('guest/home.html')

@guest_bp.route('/about')
def about():
    """Renders the 'About Us' page explaining the application."""
    return render_template('guest/about.html')