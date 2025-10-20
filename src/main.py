# main.py
import asyncio
import logging
import sys
from pathlib import Path

from cli.commands import dry_run_command, list_lines_command, show_results_command
from cli.parser import create_argument_parser
from core.config import settings
from core.database_init import check_and_initialize_database, encrypt_unencrypted_passwords
from core.executor import execute_quota_checks, execute_speed_tests, generate_and_send_report
from core.logging_config import setup_file_logging
from db.crud import CheckMode
from db.database import engine
from services.line_service import LineService

logger = logging.getLogger(__name__)


async def main(args) -> None:
    """Main application entry point"""

    # Set logging level based on verbosity
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize file-based logging
    log_file = setup_file_logging(log_dir=Path("logs"), max_files=7)

    logger.info("=" * 60)
    logger.info("NetNinja Execution Started")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 60)

    # Handle database operations (early exit commands)
    if args.setup_db:
        await check_and_initialize_database()
        await engine.dispose()
        return

    if args.list_lines:
        await list_lines_command()
        await engine.dispose()
        return

    if args.show_results:
        await show_results_command()
        await engine.dispose()
        return

    # Check and initialize database
    is_new_database = await check_and_initialize_database()
    if is_new_database:
        logger.warning(
            "🛑 Database was just created. Please add ISP lines before running the application."
        )
        logger.info("Exiting...")
        await engine.dispose()
        return

    # Encrypt any unencrypted passwords
    await encrypt_unencrypted_passwords()

    # Get all lines
    lines = await LineService.get_all_lines()
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
        dry_run_command(lines, args)
        await engine.dispose()
        return

    logger.info(f"📊 Processing {len(lines)} line(s)")

    # Determine check mode and execute tasks
    check_mode = CheckMode.FULL

    if not args.speedtest_only:
        check_mode = CheckMode.QUOTA_CHECK_ONLY if args.quota_only else CheckMode.FULL
        await execute_quota_checks(lines, args.headless)

    if not args.quota_only:
        check_mode = CheckMode.SPEED_TEST_ONLY if args.speedtest_only else check_mode
        await execute_speed_tests(lines)

    # Generate and send report
    await generate_and_send_report(lines, args, check_mode)

    await engine.dispose()


if __name__ == "__main__":
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        logger.info("\n⚠️  Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
