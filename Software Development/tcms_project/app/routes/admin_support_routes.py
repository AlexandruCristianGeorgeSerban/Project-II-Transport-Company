import logging
import sqlite3
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models.support_model import SupportModel
from app.models.notification_model import NotificationModel

admin_support_bp = Blueprint('admin_support', __name__)
support_db = SupportModel()
notif_db = NotificationModel()

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
        if support_db.add_reply(ticket_id=ticket_id, sender=role, message=response_text, sender_role=role):
            try:
                with sqlite3.connect("instance/database.sqlite") as conn:
                    conn.row_factory = sqlite3.Row
                    ticket = conn.execute("SELECT client, client_role FROM support_tickets WHERE id = ?", (ticket_id,)).fetchone()
                    
                    if ticket and ticket['client']:
                        destinatar = str(ticket['client']).strip()
                        
                        t_role = str(ticket['client_role']).strip() if 'client_role' in ticket.keys() else 'Customer'
                        t_url = f"/driver/support#ticket-{ticket_id}" if t_role == 'Driver' else f"/portal/support#ticket-{ticket_id}"
                        
                        # 🔴 TRIMITE NOTIFICARE DOAR CLIENTULUI (Sau șoferului). Fără Staff! Fără Ecou!
                        mesaj_notificare = f"💬 Echipa de suport a răspuns la tichetul tău #{ticket_id}."
                        notif_db.add_notification(destinatar, mesaj_notificare, target_url=t_url)
                        
            except Exception as e:
                logging.error(f"Eroare notificare admin support: {e}")
            
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