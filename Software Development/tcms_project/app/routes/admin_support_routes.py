import logging
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models.support_model import SupportModel

admin_support_bp = Blueprint('admin_support', __name__)
support_db = SupportModel()

@admin_support_bp.route('/admin/support')
def view_tickets() -> str:
    if session.get('role') not in ['Administrator', 'Staff']:
        return redirect(url_for('auth.login'))
    
    tickets_data = support_db.get_all_tickets()
    return render_template('admin/support_tickets.html', tickets=tickets_data, role=session.get('role'))

@admin_support_bp.route('/admin/support/respond/<int:ticket_id>', methods=['POST'])
def respond_to_ticket(ticket_id: int) -> str:
    role = session.get('role')
    if role not in ['Administrator', 'Staff']:
        return redirect(url_for('auth.login'))
    
    response_text = request.form.get('admin_reply')
    if response_text:
        # Folosim noua functie add_reply! Trece cine a dat reply-ul (Staff sau Admin)
        if support_db.add_reply(ticket_id, role, response_text):
            flash(f"Mesaj trimis cu succes în conversația #{ticket_id}!", "success")
        else:
            flash("Eroare la trimiterea mesajului.", "danger")
    
    return redirect(url_for('admin_support.view_tickets'))
@admin_support_bp.route('/admin/support/delete/<int:ticket_id>', methods=['POST'])
def delete_ticket(ticket_id: int) -> str:
    if session.get('role') not in ['Administrator', 'Staff']:
        return redirect(url_for('auth.login'))
    
    if support_db.delete_ticket(ticket_id):
        flash(f"Tichetul #{ticket_id} a fost șters.", "info")
    else:
        flash("Eroare la ștergerea tichetului.", "danger")
        
    return redirect(url_for('admin_support.view_tickets'))