# main.py
import argparse
import asyncio
import logging
import sys
from pathlib import Path

from app.quota_checker.we import WEWebScraper
from core.config import settings
from db.database import engine
from services.line_service import LineService
from services.notification_service import NotificationService
from services.quota_service import QuotaService
from services.speedtest_service import SpeedTestService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


async def check_and_initialize_database() -> bool:
    """
    Check if database exists and initialize if needed.
    Returns True if database was newly created, False if it already existed.
    """
    db_path = Path(
        settings.database.name
        if hasattr(settings.database, "name")
        else "app.db"
    )

    if not db_path.exists():
        logger.warning(f"⚠️  Database file not found: {db_path}")
        logger.info("🔧 Initializing database for the first time...")

        try:
            # Import and run setup
            from setup_database import setup_database

            await setup_database()

            logger.info("✅ Database initialized successfully!")
            logger.info(f"📁 Database location: {db_path.absolute()}")
            logger.info(
                "ℹ️  Please add your ISP lines to the database before running again."
            )
            logger.info(
                "ℹ️  You can use the admin interface or database management tools."
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            logger.error(
                "Please run 'python setup_database.py' manually to set up the database."
            )
            sys.exit(1)
    else:
        logger.info(f"✓ Database found: {db_path}")
        return False


async def bound_quota_task(line, semaphore, headless):
    """Execute quota scraping with concurrency control"""
    async with semaphore:
        await QuotaService.scrap_and_save_quota(line, headless)


async def main(headless: bool) -> None:
    # Check database on startup
    is_new_database = await check_and_initialize_database()

    if is_new_database:
        logger.warning(
            "🛑 Database was just created. Please add ISP lines before running the application."
        )
        logger.info("Exiting...")
        await engine.dispose()
        return

    # Get all lines
    lines = await LineService.get_all_lines()

    if not lines:
        logger.warning("⚠️  No lines found in database!")
        logger.info("Please add ISP lines to the database before running.")
        logger.info("Exiting...")
        await engine.dispose()
        return

    logger.info(f"📊 Found {len(lines)} line(s) to process")

    # Limit concurrent scraping tasks
    semaphore = asyncio.Semaphore(2)

    # Execute Quota Check
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

    # Execute Speed Tests
    logger.info("🚀 Starting speed tests...")
    await asyncio.gather(
        *(SpeedTestService.run_and_save_speedtest(line) for line in lines),
        return_exceptions=True,
    )

    # Get latest results and send email
    logger.info("📧 Preparing daily report...")
    latest_results = await QuotaService.get_latest_results(lines)
    await NotificationService.send_daily_report(
        subject="DailyCheck",
        sender="adel.ali@andalusiagroup.net",
        data=latest_results,
    )

    logger.info("✅ All tasks completed successfully!")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run quota check and speedtest."
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run in headless mode"
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(args.headless))
    except KeyboardInterrupt:
        logger.info("\n⚠️  Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
