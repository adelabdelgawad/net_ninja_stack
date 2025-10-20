import asyncio
import logging
from db.crud import read_lines
from tasks.quota_tasks import execute_quota_task
from tasks.speedtest_tasks import execute_speedtest_task
from app.mail import send_email
from app.quota_checker import WEWebScraper
from db.database import create_tables
from db.crud import create_isp, create_email_type
logger = logging.getLogger(__name__)


async def create_default_records():
    """
    Create default records for ISP and email types.
    """
    try:
        # Create default ISPs
        await create_isp("WE")
        await create_isp("Orange")
        await create_isp("Vodafone")
        await create_isp("Etisalat")

        # Create default email types
        await create_email_type("To")
        await create_email_type("CC")

        logger.info("Default records created successfully.")
    except Exception as e:
        logger.error(f"Failed to create default records: {e}", exc_info=True)
        raise


async def run_quota_tasks(lines, headless, semaphore):
    """
    Runs the quota check tasks for all lines with a concurrency limit.

    Args:
        lines (List[Line]): List of Line objects to check.
        headless (bool): Whether to run the scraper in headless mode.
        semaphore (asyncio.Semaphore): Semaphore to control concurrency.
    """
    try:
        logger.info("Starting quota check tasks.")
        # Run the quota tasks
        await asyncio.gather(
            *(execute_quota_task(line, semaphore, headless)
              for line in lines),
            return_exceptions=True,
        )

        # Retry failed quota tasks, if any
        if WEWebScraper.failed_list:
            logger.warning(f"Retrying failed quota tasks for {
                           len(WEWebScraper.failed_list)} lines.")
            await asyncio.gather(
                *(execute_quota_task(line, semaphore, headless)
                  for line in WEWebScraper.failed_list),
                return_exceptions=True,
            )
    except Exception as ex:
        logger.error(f"Error while running quota tasks: {ex}")
        raise


async def run_speedtest_tasks(lines, semaphore):
    """
    Runs the speedtest tasks for all lines with a concurrency limit.

    Args:
        lines (List[Line]): List of Line objects to run speed tests on.
        semaphore (asyncio.Semaphore): Semaphore to control concurrency.
    """
    try:
        logger.info("Starting speedtest tasks.")
        await asyncio.gather(
            *(execute_speedtest_task(semaphore, line) for line in lines),
            return_exceptions=True
        )
    except Exception as ex:
        logger.error(f"Error while running speedtest tasks: {ex}")
        raise


async def run_tasks(headless: bool) -> None:
    """
    Orchestrates the execution of quota checks, speedtests, and result emails for all lines.

    Args:
        engine: The database engine to use for database operations.
        headless (bool): Whether to run the scraper in headless mode.
    """
    # Create necessary tables
    await create_tables()

    # Create a session and manage connection lifecycle
    await create_default_records()  # Initialize default records

    # Retrieve lines from the database
    lines = await read_lines()
    if not lines:
        logger.info(
            "No lines found. Please add lines to the local database.")
        return

    # Limit concurrency for tasks using semaphore
    semaphore = asyncio.Semaphore(2)

    try:
        # Step 1: Run Quota Check Tasks
        logger.info("Running quota check tasks.")
        await run_quota_tasks(lines, headless, semaphore)

        # Step 2: Run Speedtest Tasks
        logger.info("Running speedtest tasks.")
        await run_speedtest_tasks(lines, semaphore)

        # Step 3: Send Results via Email
        logger.info("Sending email with the results.")
        await send_email(lines)

    except Exception as ex:
        logger.error(
            f"An error occurred during the task execution: {ex}")
        raise
