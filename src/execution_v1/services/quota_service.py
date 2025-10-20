# services/quota_service.py
import logging
from typing import List, Optional

from app.quota_checker.orange import OrangeWebScraper
from app.quota_checker.we import WEWebScraper
from db.database import get_session
from db.model import Line, QuotaResult
from db.models import QuotaResultModel

logger = logging.getLogger(__name__)


class QuotaService:
    """Service for handling quota scraping and storage"""

    @staticmethod
    async def scrap_and_save_quota(
        line: Line, headless: bool = False
    ) -> Optional[QuotaResult]:
        """
        Scrape quota data for a line and save to database.

        Args:
            line: Line object containing ISP and portal credentials
            headless: Whether to run browser in headless mode

        Returns:
            Saved QuotaResult or None if failed
        """
        try:
            # Map ISP ID to scraper class
            scraper_map = {
                1: WEWebScraper,
                2: OrangeWebScraper,
            }

            # Get appropriate scraper class
            scraper_class = scraper_map.get(line.isp_id)

            if not scraper_class:
                logger.warning(
                    f"Unsupported ISP ID {line.isp_id} for {line.name}"
                )
                return None

            # Scrape the data
            async with scraper_class(line, headless) as scraper:
                if not await scraper.login():
                    logger.error(f"Login failed for {line.name}")
                    return None

                # WE ISP uses different page methods
                if line.isp_id == 1:
                    await scraper.scrap_overview_page()
                    await scraper.scrap_renewaldate_page()
                # Orange ISP uses different page methods
                elif line.isp_id == 2:
                    await scraper.scrap_balance_page()
                    await scraper.scrap_internet_page()

            # Save to database
            async with get_session() as session:
                quota_model = QuotaResultModel(session)
                result = await quota_model.create(scraper.result)
                logger.info(
                    f"Successfully saved quota result for {line.name} "
                    f"with ID {result.id}"
                )
                return result

        except Exception as e:
            logger.error(f"Error scraping quota for {line.name}: {e}")
            return None

    @staticmethod
    async def get_latest_results(lines: List[Line]) -> List[QuotaResult]:
        """
        Get the latest quota results for multiple lines.

        Args:
            lines: List of Line objects

        Returns:
            List of latest QuotaResult objects
        """
        results = []
        async with get_session() as session:
            quota_model = QuotaResultModel(session)
            for line in lines:
                result = await quota_model.read_last_record(line_id=line.id)
                if result:
                    results.append(result)
        return results
