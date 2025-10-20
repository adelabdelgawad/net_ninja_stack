import asyncio
import logging
import re
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium_async import Options, launch

from app.wait import WebDriverWait
from core.scraper_config import timeouts, we_selectors
from db.model import Line, QuotaResult

logger = logging.getLogger(__name__)


# WEWebScraper class
class WEWebScraper:
    """WE Scraping Base Class"""

    failed_list = []

    def __init__(
        self,
        line: Line,
        headless: Optional[bool] = False,
    ) -> None:
        """Initialize with line details and headless option"""
        self.line = line
        self.headless = headless

        # Page contents
        self.overview_page_content = None
        self.renewaldate_page_content = None

        # Parsed values
        self.used = None
        self.remaining = None
        self.balance = None
        self.used_perc = None
        self.renewal_date = None
        self.remaining_days = None
        self.renewal_cost = None
        self.succeed = False

    async def __aenter__(self):
        logger.info(f"Launching browser for {self.line.name}")
        self.driver = await launch(options=Options(headless=self.headless))
        return self

    async def __aexit__(self, *args, **kwargs):
        logger.info(f"Closing browser for {self.line.name}")
        self.driver.quit()
        if not self.succeed:
            logger.warning(f"Scraping failed for {self.line.name}")
            if self.line not in self.failed_list:
                self.failed_list.append(self.line)
        self.result = QuotaResult(
            line_id=self.line.id,
            data_used=self.used,
            usage_percentage=self.used_perc,
            data_remaining=self.remaining,
            balance=self.balance,
            renewal_date=self.renewal_date,
            remaining_days=self.remaining_days,
            renewal_cost=self.renewal_cost,
        )

    async def login(self) -> bool:
        try:
            logger.info(f"Logging in for {self.line.name}")
            self.driver.get("https://my.te.eg/user/login")
            await WebDriverWait(self.driver, timeouts.login_wait).until(
                EC.presence_of_element_located(
                    (By.ID, we_selectors.login_id)
                )
            )

            # Input credentials
            self.driver.find_element(By.ID, we_selectors.login_id).click()
            self.driver.find_element(
                By.ID, we_selectors.login_id
            ).send_keys(self.line.portal_username)
            self.driver.find_element(By.ID, we_selectors.login_type).click()
            self.driver.find_element(
                By.CSS_SELECTOR,
                we_selectors.account_type_selector,
            ).click()
            self.driver.find_element(By.ID, we_selectors.login_password).click()
            self.driver.find_element(
                By.ID, we_selectors.login_password
            ).send_keys(self.line.get_password())  # Use decrypted password
            self.driver.find_element(By.ID, we_selectors.login_button).click()
            await asyncio.sleep(timeouts.post_action_delay)
            logger.info(f"{self.line.name} logged in successfully")
            return True
        except Exception as e:
            logger.error(f"Login failed for {self.line.name}: {e}")
            return False

    async def scrap_overview_page(self) -> bool:
        logger.info(f"Navigating to overview page for {self.line.name}")
        await asyncio.sleep(1)  # Adjust based on observed page load times
        try:
            self.driver.get("https://my.te.eg/offering/overview")
            await asyncio.sleep(timeouts.post_action_delay)

            await WebDriverWait(self.driver, timeouts.page_load_wait).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, we_selectors.balance)
                )
            )
            logger.debug(f"Overview page loaded successfully for {self.line.name}")

            await asyncio.sleep(timeouts.element_wait)

            # Extracting values from the page
            self.balance = self.driver.find_element(
                By.CSS_SELECTOR, we_selectors.balance
            ).text.replace(",", "")
            self.used = float(
                self.driver.find_element(
                    By.CSS_SELECTOR, we_selectors.data_used
                ).text.replace(",", "")
            )
            self.remaining = float(
                self.driver.find_element(
                    By.CSS_SELECTOR, we_selectors.data_remaining
                ).text.replace(",", "")
            )
            self.used_perc = await self._calc_used_perc(
                self.used, self.remaining
            )

            logger.info(
                f"Extracted values for {self.line.name} - Balance: {self.balance}, Used: {self.used}, Remaining: {self.remaining}, Usage Percentage: {self.used_perc}%"
            )
            self.succeed = True
            return True
        except Exception as e:
            logger.error(
                f"Error extracting overview page for {self.line.name}: {e}"
            )
            return False

    async def scrap_renewaldate_page(self) -> bool:
        logger.info(f"Navigating to renewal page for {self.line.name}")

        try:
            self.driver.get("https://my.te.eg/echannel/#/overview")

            await WebDriverWait(self.driver, timeouts.page_load_wait).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, we_selectors.renewal_cost)
                )
            )
            await asyncio.sleep(timeouts.element_wait)
            logger.debug(f"Renewal page loaded successfully for {self.line.name}")

            # Extracting renewal cost and date
            self.renewal_cost = float(
                self.driver.find_element(
                    By.CSS_SELECTOR, we_selectors.renewal_cost
                ).text.replace(",", "")
            )
            renewal_date_element = self.driver.find_element(
                By.CSS_SELECTOR, we_selectors.renewal_date
            ).text
            await self._set_renewal_date(renewal_date_element)

            logger.info(
                f"Extracted renewal cost and date for {self.line.name} - Renewal Cost: {self.renewal_cost}, Renewal Date: {self.renewal_date}, Remaining Days: {self.remaining_days}"
            )
            self.succeed = True
            return True
        except Exception as e:
            logger.error(
                f"Error extracting renewal page for {self.line.name}: {e}"
            )
            return False

    async def _set_renewal_date(self, renewal_date_element: str):
        logger.debug(f"Setting renewal date for {self.line.name}")
        try:
            if renewal_date_element:
                match = re.search(
                    r"Renewal Date: (\d{2}-\d{2}-\d{4}), (\d+) Remaining Days",
                    renewal_date_element,
                )
                if match:
                    self.renewal_date = match.group(1)
                    self.remaining_days = int(match.group(2))
        except Exception as e:
            logger.error(
                f"Error setting renewal date for {self.line.name}: {e}"
            )

    async def _calc_used_perc(self, used: float, remaining: float) -> float:
        try:
            total = used + remaining
            return (used / total) * 100
        except ZeroDivisionError:
            logger.error(
                f"Division by zero error for {self.line.name}. Used: {used}, Remaining: {remaining}"
            )
            return 0.0
