# services/notification_service.py
import asyncio
import logging
from typing import List

import icecream

from app.mail import send_email
from db.database import get_session
from db.models.email_model import EmailModel
from db.models.quota_result_model import QuotaResultModel
from services.report_service import ReportService

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling notifications with retry logic and fallback"""

    @staticmethod
    async def send_daily_report(
        subject: str,
        sender: str,
        data: List[QuotaResultModel],
        max_retries: int = 3,
    ) -> bool:
        """
        Send daily report email with quota results. Includes retry logic and local fallback.

        Args:
            subject: Email subject
            sender: Sender email address
            data: List of QuotaResult objects to include in report
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            True if email sent successfully, False if fallback used
        """
        async with get_session() as session:
            email_model = EmailModel(session)
            recipients = await email_model.read_all()
            recipient_emails = [r.recipient for r in recipients]

        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                await send_email(subject, recipient_emails, sender, data)
                logger.info("Email sent successfully")
                return True
            except Exception as e:
                logger.warning(
                    f"Email attempt {attempt + 1}/{max_retries} failed: {e}"
                )
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # 1s, 2s, 4s exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

        # Fallback: Save local report
        try:
            filepath = await ReportService.save_local_report(data)
            logger.error(f"Email failed after {max_retries} attempts")
            logger.info(f"Local report saved: {filepath}")
            return False
        except Exception as e:
            logger.error(f"Failed to save local report: {e}")
            return False
