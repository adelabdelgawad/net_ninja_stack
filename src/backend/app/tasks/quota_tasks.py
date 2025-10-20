import asyncio
import logging
from db.crud import create_process, create_quota_result
from app.quota_checker import WEWebScraper
from db.schema import Line, QuotaResultCreate

logger = logging.getLogger(__name__)


async def scrape_quota_information(
    line: Line,
    run_headless: bool = False
) -> None:
    """
    Scrapes the quota information for the given line and stores the result in the database.

    Args:
        line (Line): The Line object representing the internet line to scrape data for.
        run_headless (bool): Whether to run the browser in headless mode (without a UI).
    """
    # Create a new process record in the database for tracking the scraping activity
    process = await create_process(line.id)

    # If the ISP is 'WE' (ID = 1), use the WEWebScraper to retrieve quota information
    if line.isp_id == 1:
        logger.error("Starting WebScraping for 'WE' Line")
        async with WEWebScraper(process.id, line, run_headless) as scraper:
            try:
                if await scraper.login():
                    await scraper.scrape_overview_page()
                    await scraper.scrape_renewal_date_page()

                # After successful scraping, create a quota result record
                result = QuotaResultCreate(
                    process_id=process.id,
                    line_id=line.id,
                    data_used=scraper.used,
                    usage_percentage=scraper.usage_percentage,
                    data_remaining=scraper.remaining,
                    balance=scraper.balance,
                    renewal_date=scraper.renewal_date,
                    remaining_days=scraper.remaining_days,
                    renewal_cost=scraper.renewal_cost,
                )
                await create_quota_result(result)

            except Exception as ex:
                logger.error(f"Error during scraping for line {line.id}: {ex}")
                # You might want to handle the exception further or report it to the process log
                raise str(ex)


async def execute_quota_task(
    line: Line,
    concurrency_limiter: asyncio.Semaphore,
    run_headless: bool
) -> None:
    """
    Executes the quota scraping task with a semaphore for concurrency control.

    Args:
        line (Line): The Line object representing the internet line to scrape.
        concurrency_limiter (asyncio.Semaphore): A semaphore to limit the number of concurrent tasks.
        run_headless (bool): Whether to run the browser in headless mode (without a UI).
    """
    async with concurrency_limiter:
        await scrape_quota_information(line, run_headless)
