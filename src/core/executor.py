# core/executor.py
import asyncio
import logging
from typing import List

from app.quota_checker.we import WEWebScraper
from core.config import settings
from db.crud import CheckMode, read_last_result
from db.database import get_session
from db.model import Line
from services.notification_service import NotificationService
from services.quota_service import QuotaService
from services.report_service import ReportService
from services.speedtest_service import SpeedTestService

logger = logging.getLogger(__name__)


async def bound_quota_task(line: Line, semaphore: asyncio.Semaphore, headless: bool):
    """Execute quota scraping with concurrency control"""
    async with semaphore:
        await QuotaService.scrap_and_save_quota(line, headless)


async def execute_quota_checks(lines: List[Line], headless: bool):
    """Execute quota checks for all lines with retry logic"""
    semaphore = asyncio.Semaphore(settings.execution.semaphore_limit)

    logger.info("🔍 Starting quota checks...")
    await asyncio.gather(
        *(bound_quota_task(line, semaphore, headless) for line in lines),
        return_exceptions=True,
    )

    # Retry failed tasks
    if WEWebScraper.failed_list:
        logger.info(
            f"🔄 Retrying {len(WEWebScraper.failed_list)} failed quota check(s)..."
        )
        await asyncio.gather(
            *(
                bound_quota_task(line, semaphore, headless)
                for line in WEWebScraper.failed_list
            ),
            return_exceptions=True,
        )


async def execute_speed_tests(lines: List[Line]):
    """Execute speed tests for all lines"""
    logger.info("🚀 Starting speed tests...")
    await asyncio.gather(
        *(SpeedTestService.run_and_save_speedtest(line) for line in lines),
        return_exceptions=True,
    )


async def generate_and_send_report(lines: List[Line], args, check_mode: CheckMode):
    """Generate report and send via email or save to file"""
    logger.info("📧 Preparing daily report...")

    # Get latest results
    async with get_session() as session:
        latest_results = [
            await read_last_result(session=session, line=line, mode=check_mode)
            for line in lines
        ]

    if args.output:
        # Save to file
        await ReportService.save_report(latest_results, args.output, args.format)
        logger.info(f"📄 Report saved to: {args.output}")
    elif not args.no_email:
        # Send email
        email_success = await NotificationService.send_daily_report(
            subject=settings.email.subject,
            sender=settings.email.sender,
            data=latest_results,
        )

        if email_success:
            logger.info("✅ All tasks completed successfully!")
        else:
            logger.warning(
                "⚠️  Tasks completed but email delivery failed. Check reports/ directory."
            )
    else:
        logger.info("✅ Tasks completed (email skipped)")
