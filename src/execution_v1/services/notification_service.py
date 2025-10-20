# services/notification_service.py
from typing import List

from app.mail import send_email
from db.database import get_session
from db.model import QuotaResult
from db.models import EmailModel


class NotificationService:
    """Service for handling notifications"""

    @staticmethod
    async def send_daily_report(
        subject: str, sender: str, data: List[QuotaResult]
    ) -> None:
        """
        Send daily report email with quota results.

        Args:
            subject: Email subject
            sender: Sender email address
            data: List of QuotaResult objects to include in report
        """
        async with get_session() as session:
            email_model = EmailModel(session)
            recipients = await email_model.read_all()
            recipient_emails = [r.recipient for r in recipients]

        await send_email(subject, recipient_emails, sender, data)
