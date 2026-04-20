import logging
from typing import List, Dict, Any
from app.models.notification_model import NotificationModel

class NotificationController:
    """Processes logic for system notifications."""

    def __init__(self):
        self.model = NotificationModel()
        self.model.create_table()

    def get_user_notifications(self, role: str) -> List[Dict[str, Any]]:
        """Returns a list of unread notifications for a specific role."""
        return self.model.get_unread_notifications(role)

    def mark_notification_as_read(self, notif_id: int) -> bool:
        """Marks a specific notification as read."""
        try:
            self.model.mark_as_read(notif_id)
            return True
        except Exception as e:
            logging.error(f"Error in controller marking read: {e}")
            return False