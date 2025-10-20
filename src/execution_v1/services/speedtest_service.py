# services/speedtest_service.py
import logging
from typing import Optional

from app.async_speedtest import AsyncSpeedtest
from db.database import get_session
from db.model import Line, SpeedTestResult
from db.models import SpeedTestResultModel

logger = logging.getLogger(__name__)


class SpeedTestService:
    """Service for handling speed tests and storage"""

    @staticmethod
    async def run_and_save_speedtest(line: Line) -> Optional[SpeedTestResult]:
        """
        Run speed test for a line and save to database.

        Args:
            line: Line object with IP address

        Returns:
            Saved SpeedTestResult or None if failed
        """
        st = AsyncSpeedtest(line.ip_address)
        download = 0.0
        upload = 0.0

        try:
            await logger.info(st.process_id, "Getting Configurations")
            if await st.get_config():
                await logger.info(st.process_id, "Finding best server")
                await st.get_best_server()

                await logger.info(st.process_id, "Measuring latency")
                await st.measure_latency()

                await logger.info(st.process_id, "Starting download test")
                await st.measure_download_speed()

                await logger.info(st.process_id, "Starting upload test")
                await st.measure_upload_speed()

                download = round(st.download * 8 / (1024 * 1024), 2)
                upload = round(st.upload * 8 / (1024 * 1024), 2)
            else:
                await logger.error(
                    st.process_id, "Could not connect to Ookla's Servers."
                )
        finally:
            # Save result regardless of success/failure
            result = SpeedTestResult(
                line_id=line.id,
                process_id=st.process_id,
                ping=st.ping,
                upload_speed=upload,
                download_speed=download,
                public_ip=st.public_ip,
            )

            async with get_session() as session:
                speedtest_model = SpeedTestResultModel(session)
                saved_result = await speedtest_model.create(result)
                logger.info(
                    f"Saved speedtest result for {line.name} with ID {saved_result.id}"
                )
                return saved_result
