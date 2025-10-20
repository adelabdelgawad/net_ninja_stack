# main.py
import argparse
import asyncio
import logging
import sys
from pathlib import Path

from app.quota_checker.we import WEWebScraper
from core.config import settings
from core.logging_config import setup_file_logging
from db.crud import CheckMode, read_last_result
from db.database import engine, get_session
from db.models.line_model import LineModel
from services.line_service import LineService
from services.notification_service import NotificationService
from services.quota_service import QuotaService
from services.speedtest_service import SpeedTestService

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


async def display_last_results():
    """Display last results in terminal"""
    from db.database import get_session
    from db.models import QuotaResultModel, SpeedTestResultModel

    lines = await LineService.get_all_lines()
    print(
        f"\n{'Line':<20} {'Used':<20} {'Remaining':<15} {'Download':<12} {'Upload':<12} {'Ping':<10}"
    )
    print("-" * 90)

    for line in lines:
        async with get_session() as session:
            quota_model = QuotaResultModel(session)
            speed_model = SpeedTestResultModel(session)

            quota = await quota_model.read_last_record(line_id=line.id)
            speed = await speed_model.read_last_record(line_id=line.id)

            used = (
                f"{quota.data_used}GB ({quota.usage_percentage}%)"
                if quota and quota.data_used
                else "-"
            )
            remaining = (
                f"{quota.data_remaining}GB"
                if quota and quota.data_remaining
                else "-"
            )
            download = (
                f"{speed.download_speed}Mbps"
                if speed and speed.download_speed
                else "-"
            )
            upload = (
                f"{speed.upload_speed}Mbps"
                if speed and speed.upload_speed
                else "-"
            )
            ping = f"{speed.ping}ms" if speed and speed.ping else "-"

            print(
                f"{line.name:<20} {used:<20} {remaining:<15} {download:<12} {upload:<12} {ping:<10}"
            )


async def main(args) -> None:
    # Set logging level based on verbosity
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize file-based logging at startup
    log_file = setup_file_logging(log_dir=Path("logs"), max_files=7)

    logger.info("=" * 60)
    logger.info("NetNinja Execution Started")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 60)

    # Database operations (exit after)
    if args.setup_db:
        await check_and_initialize_database()
        await engine.dispose()
        return

    if args.list_lines:
        lines = await LineService.get_all_lines()
        print(f"\n{'ID':<5} {'Name':<20} {'ISP':<15} {'IP Address':<15}")
        print("-" * 60)
        for line in lines:
            print(
                f"{line.id:<5} {line.name:<20} {line.isp.name:<15} {line.ip_address:<15}"
            )
        await engine.dispose()
        return

    if args.show_results:
        await display_last_results()
        await engine.dispose()
        return

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
    async with get_session() as session:
        line_model = LineModel(session)

        for line in lines:
            # Check if password is encrypted
            if line.portal_password and not line.portal_password.startswith(
                "gAAAAA"
            ):
                # Encrypt and update the password in the line object
                line.set_password(line.portal_password)
                # Update the record in the DB
                await line_model.update(
                    line.id, {"portal_password": line.portal_password}
                )

        if not lines:
            logger.warning("⚠️  No lines found in database!")
            logger.info("Please add ISP lines to the database before running.")
            logger.info("Exiting...")
            await engine.dispose()
            return

    # Apply filters
    if args.line_id:
        lines = [l for l in lines if l.id == args.line_id]
        if not lines:
            logger.error(f"Line ID {args.line_id} not found")
            await engine.dispose()
            return

    if args.isp:
        lines = [l for l in lines if l.isp.name.lower() == args.isp.lower()]

    if not lines:
        logger.warning("No lines found matching filters")
        await engine.dispose()
        return

    # Dry run mode
    if args.dry_run:
        print(f"\n🔍 DRY RUN MODE - Would execute:")
        print(f"  Lines: {len(lines)}")
        for line in lines:
            print(f"    - {line.name} ({line.isp.name})")
        if not args.speedtest_only:
            print(f"  ✓ Quota checks (headless: {args.headless})")
        if not args.quota_only:
            print(f"  ✓ Speed tests")
        if not args.no_email:
            print(f"  ✓ Email notification")
        await engine.dispose()
        return

    logger.info(f"📊 Processing {len(lines)} line(s)")

    # Limit concurrent scraping tasks
    semaphore = asyncio.Semaphore(settings.execution.semaphore_limit)

    # Execute based on mode
    check_mode = CheckMode.FULL
    if not args.speedtest_only:
        check_mode = CheckMode.QUOTA_CHECK_ONLY
        logger.info("🔍 Starting quota checks...")
        await asyncio.gather(
            *(
                bound_quota_task(line, semaphore, args.headless)
                for line in lines
            ),
            return_exceptions=True,
        )

        # Retry failed tasks
        if WEWebScraper.failed_list:
            logger.info(
                f"🔄 Retrying {len(WEWebScraper.failed_list)} failed quota check(s)..."
            )
            await asyncio.gather(
                *(
                    bound_quota_task(line, semaphore, args.headless)
                    for line in WEWebScraper.failed_list
                ),
                return_exceptions=True,
            )

    if not args.quota_only:
        check_mode = CheckMode.SPEED_TEST_ONLY
        logger.info("🚀 Starting speed tests...")
        await asyncio.gather(
            *(SpeedTestService.run_and_save_speedtest(line) for line in lines),
            return_exceptions=True,
        )

    # Generate report
    logger.info("📧 Preparing daily report...")
    async with get_session() as session:
        latest_results = [
            await read_last_result(session=session, line=line, mode=check_mode)
            for line in lines
        ]

    if args.output:
        # Save to file
        from services.report_service import ReportService

        await ReportService.save_report(
            latest_results, args.output, args.format
        )
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

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NetNinja - Network Monitoring for Egyptian ISPs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --headless                    # Run all checks headless
  %(prog)s --quota-only                  # Only check quota (skip speedtest)
  %(prog)s --speedtest-only              # Only run speedtest (skip quota)
  %(prog)s --no-email                    # Run checks but don't send email
  %(prog)s --dry-run                     # Show what would run without executing
  %(prog)s --line-id 1                   # Run for specific line only
  %(prog)s --verbose                     # Detailed output
  %(prog)s --quiet                       # Minimal output
  %(prog)s --output report.html          # Save report to file instead of email
  %(prog)s --list-lines                  # List all configured lines
  %(prog)s --show-results                # Show last results
        """,
    )

    # Execution modes
    mode_group = parser.add_argument_group("Execution Modes")
    mode_group.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (no GUI)",
    )
    mode_group.add_argument(
        "--quota-only",
        action="store_true",
        help="Only perform quota checks (skip speedtest)",
    )
    mode_group.add_argument(
        "--speedtest-only",
        action="store_true",
        help="Only perform speed tests (skip quota)",
    )
    mode_group.add_argument(
        "--no-email",
        action="store_true",
        help="Skip email notification (save to file instead)",
    )
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running",
    )

    # Filtering
    filter_group = parser.add_argument_group("Filtering")
    filter_group.add_argument(
        "--line-id",
        type=int,
        metavar="ID",
        help="Run for specific line ID only",
    )
    filter_group.add_argument(
        "--isp",
        choices=["WE", "Orange", "Vodafone", "Etisalat"],
        help="Run for specific ISP only",
    )

    # Output control
    output_group = parser.add_argument_group("Output Control")
    output_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output (show all details)",
    )
    output_group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode (minimal output)",
    )
    output_group.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Save report to file instead of sending email",
    )
    output_group.add_argument(
        "--format",
        choices=["html", "json", "csv"],
        default="html",
        help="Output format (default: html)",
    )

    # Database operations
    db_group = parser.add_argument_group("Database Operations")
    db_group.add_argument(
        "--setup-db", action="store_true", help="Initialize database and exit"
    )
    db_group.add_argument(
        "--list-lines",
        action="store_true",
        help="List all configured lines and exit",
    )
    db_group.add_argument(
        "--show-results",
        action="store_true",
        help="Show last results and exit",
    )

    args = parser.parse_args()

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        logger.info("\n⚠️  Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
