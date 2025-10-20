from db.crud import create_process, create_speed_test_result, create_log
from app.async_speedtest import AsyncSpeedtest
from db.schema import Line, SpeedTestResultCreate
import logging
import asyncio
logger = logging.getLogger(__name__)


async def _run_speedtest(line: Line) -> None:
    """
    Runs a speed test for the given line and stores the result in the database.

    Args:
        line (Line): The Line object to test.
    """
    process = await create_process(line.id)

    st = AsyncSpeedtest(process.id, line.ip_address)

    try:
        if await st.get_config():
            await st.get_best_server()
            await st.measure_latency()
            await st.measure_download_speed()
            await st.measure_upload_speed()

            result = SpeedTestResultCreate(
                line_id=line.id,
                process_id=st.process_id,
                ping=st.ping,
                upload_speed=st.upload,
                download_speed=st.download,
                public_ip=st.public_ip,
            )
            await create_speed_test_result(result)
        else:
            await create_log(
                process.id,
                f"{line.ip_address}: Could not connect to Ookla's Servers.",
            )
    except Exception as e:
        logger.error(
            f"Failed to run speedtest for {line.ip_address}: {e}", exc_info=True
        )


async def execute_speedtest_task(
    concurrency_limiter: asyncio.Semaphore,
    line: Line,
) -> None:
    """
    Executes the quota scraping task with a semaphore for concurrency control.

    Args:
        line (Line): The Line object representing the internet line to scrape.
        concurrency_limiter (asyncio.Semaphore): A semaphore to limit the number of concurrent tasks.
        run_headless (bool): Whether to run the browser in headless mode (without a UI).
    """
    async with concurrency_limiter:
        await _run_speedtest(line)
