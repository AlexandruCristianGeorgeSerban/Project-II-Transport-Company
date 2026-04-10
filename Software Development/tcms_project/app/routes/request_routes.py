import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.controllers.request_controller import RequestController

request_bp = Blueprint('request_routes', __name__)
req_logic = RequestController()

@request_bp.route('/requests', methods=['GET'])
def request_management() -> str:
    """Renders the main Transport Requests page."""
    if 'user_id' not in session:
        flash("Please log in.", "danger")
        return redirect(url_for('auth.login'))
    
    view_data = req_logic.load_request_data()
    role = session.get('role', 'Staff')
    
    return render_template('admin/requests.html', data=view_data, role=role)

@request_bp.route('/requests/add', methods=['POST'])
def add_request() -> str:
    """Handles adding a new transport request."""
    r_id = request.form.get('request_id')
    client = request.form.get('client_name')
    c_type = request.form.get('cargo_type')
    desc = request.form.get('description')
    weight = float(request.form.get('weight', 0.0))
    volume = float(request.form.get('volume', 0.0))
    pickup = request.form.get('pickup')
    delivery = request.form.get('delivery')
    date = request.form.get('preferred_date')
    status = request.form.get('status')
    
    resp = req_logic.add_new_request(r_id, client, c_type, desc, weight, volume, pickup, delivery, date, status)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('request_routes.request_management'))

@request_bp.route('/requests/edit', methods=['POST'])
def edit_request() -> str:
    """Handles editing an existing transport request."""
    r_id = request.form.get('edit_request_id')
    client = request.form.get('edit_client_name')
    c_type = request.form.get('edit_cargo_type')
    desc = request.form.get('edit_description')
    weight = float(request.form.get('edit_weight', 0.0))
    volume = float(request.form.get('edit_volume', 0.0))
    pickup = request.form.get('edit_pickup')
    delivery = request.form.get('edit_delivery')
    date = request.form.get('edit_preferred_date')
    status = request.form.get('edit_status')
    
    resp = req_logic.modify_request(r_id, client, c_type, desc, weight, volume, pickup, delivery, date, status)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('request_routes.request_management'))

@request_bp.route('/requests/delete/<req_id>', methods=['POST'])
def delete_request(req_id: str) -> str:
    """Handles deleting a transport request."""
    resp = req_logic.remove_request(req_id)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('request_routes.request_management'))