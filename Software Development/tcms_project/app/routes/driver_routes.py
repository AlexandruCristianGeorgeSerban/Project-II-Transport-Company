import logging
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.controllers.driver_controller import DriverController

driver_bp = Blueprint('driver', __name__)
driver_logic = DriverController()

@driver_bp.route('/drivers', methods=['GET'])
def driver_management() -> str:
    """Renders the main Driver Management page."""
    if 'user_id' not in session:
        flash("Please log in.", "danger")
        return redirect(url_for('auth.login'))
    
    view_data = driver_logic.load_driver_data()
    role = session.get('role', 'Staff')
    
    return render_template('admin/drivers.html', data=view_data, role=role)

@driver_bp.route('/drivers/add', methods=['POST'])
def add_driver() -> str:
    """Handles adding a driver."""
    d_id = request.form.get('driver_id')
    name = request.form.get('name')
    status = request.form.get('status')
    exp = request.form.get('experience')
    dob = request.form.get('dob')
    doc_id = request.form.get('document_id')
    address = request.form.get('address')
    avail = request.form.get('availability')
    
    # Checkboxes send a list in Flask
    licenses_list = request.form.getlist('licenses')
    licenses_str = ", ".join(licenses_list)
    
    resp = driver_logic.add_new_driver(d_id, name, status, licenses_str, exp, dob, doc_id, address, avail)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('driver.driver_management'))

@driver_bp.route('/drivers/edit', methods=['POST'])
def edit_driver() -> str:
    """Handles editing a driver."""
    d_id = request.form.get('edit_driver_id')
    name = request.form.get('edit_name')
    status = request.form.get('edit_status')
    exp = request.form.get('edit_experience')
    dob = request.form.get('edit_dob')
    doc_id = request.form.get('edit_document_id')
    address = request.form.get('edit_address')
    avail = request.form.get('edit_availability')
    
    licenses_list = request.form.getlist('edit_licenses')
    licenses_str = ", ".join(licenses_list)
    
    resp = driver_logic.modify_driver(d_id, name, status, licenses_str, exp, dob, doc_id, address, avail)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('driver.driver_management'))

@driver_bp.route('/drivers/delete/<driver_id>', methods=['POST'])
def delete_driver(driver_id: str) -> str:
    """Handles deleting a driver."""
    resp = driver_logic.remove_driver(driver_id)
    flash(resp.get("message"), "success" if resp.get("success") else "danger")
    return redirect(url_for('driver.driver_management'))