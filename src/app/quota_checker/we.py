import asyncio
import logging
import re
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium_async import Options, launch

from app.wait import WebDriverWait
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
        self.usage_percentage = None
        self.renewal_date = None
        self.remaining_days = None
        self.renewal_cost = None
        self.succeed = False

    async def __aenter__(self):
        logger.info(f"Launching browser for {self.line.name}")
        self.driver = await launch(options=Options(headless=self.headless))
        return self

    async def __aexit__(self, *args, **kwargs):
        logger.info(f"Closing browser for {self.line.name}.")
        self.driver.quit()
        if not self.succeed:
            logger.warning(f"Scraping failed for {self.line.name}.")
            if self.line not in self.failed_list:
                self.failed_list.append(self.line)

        self.result = QuotaResult(
            line_id=self.line.id,
            data_used=self.used,
            usage_percentage=self.usage_percentage,
            data_remaining=self.remaining,
            balance=self.balance,
            renewal_date=self.renewal_date,
            remaining_days=self.remaining_days,
            renewal_cost=self.renewal_cost,
        )

    async def login(self) -> bool:
        try:
            logger.info(f"Logging in for {self.line.name}.")
            self.driver.get("https://my.te.eg/user/login")
            await WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.ID, "login_loginid_input_01")
                )
            )

            # Input credentials
            self.driver.find_element(By.ID, "login_loginid_input_01").click()
            self.driver.find_element(
                By.ID, "login_loginid_input_01"
            ).send_keys(self.line.portal_username)
            self.driver.find_element(By.ID, "login_input_type_01").click()
            self.driver.find_element(
                By.CSS_SELECTOR,
                ".ant-select-item-option-active .ant-space-item:nth-child(2) > span",
            ).click()
            self.driver.find_element(By.ID, "login_password_input_01").click()
            self.driver.find_element(
                By.ID, "login_password_input_01"
            ).send_keys(self.line.get_password())
            self.driver.find_element(By.ID, "login-withecare").click()
            await asyncio.sleep(0.5)
            logger.info(f"{self.line.name} logged in successfully.")
            return True
        except Exception as e:
            logger.error(f"Login failed for {self.line.name}: {e}")
            return False

    async def scrap_overview_page(self) -> bool:
        logger.info(f"Navigating to overview page for {self.line.name}.")
        await asyncio.sleep(1)  # Adjust based on observed page load times
        try:
            self.driver.get("https://my.te.eg/offering/overview")
            await asyncio.sleep(0.5)
            _balance_selector = "#_bes_window > main > div > div > div.ant-row > div:nth-child(2) > div > div > div > div > div:nth-child(3) > div:nth-child(1)"
            _used_selector = "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-24 > div > div > div.ant-row.ec_accountoverview_primaryBtn_Qyg-Vp > div:nth-child(2) > div > div > div.slick-list > div > div.slick-slide.slick-active.slick-current > div > div > div > div > div:nth-child(2) > div:nth-child(2) > span:nth-child(1)"
            _remaining_selector = "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-24 > div > div > div.ant-row.ec_accountoverview_primaryBtn_Qyg-Vp > div:nth-child(2) > div > div > div.slick-list > div > div.slick-slide.slick-active.slick-current > div > div > div > div > div:nth-child(2) > div:nth-child(1) > span:nth-child(1)"

            await WebDriverWait(self.driver, 7).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, _balance_selector)
                )
            )
            logger.debug(
                f"Overview page loaded successfully for {
                         self.line.name}."
            )

            await asyncio.sleep(2)

            # Extracting values from the page
            self.balance = self.driver.find_element(
                By.CSS_SELECTOR, _balance_selector
            ).text.replace(",", "")
            self.used = float(
                self.driver.find_element(
                    By.CSS_SELECTOR, _used_selector
                ).text.replace(",", "")
            )
            self.remaining = float(
                self.driver.find_element(
                    By.CSS_SELECTOR, _remaining_selector
                ).text.replace(",", "")
            )
            self.usage_percentage = await self._calc_usage_percentage(
                self.used, self.remaining
            )
            logger.info(
                f"Extracted values for {self.line.name} - Balance: {self.balance}, Used: {
                    self.used}, Remaining: {self.remaining}, Usage Percentage: {self.usage_percentage}%"
            )
            self.succeed = True
            return True
        except Exception as e:
            logger.error(
                f"Error extracting overview page for {
                         self.line.name}: {e}"
            )
            return False

    async def scrap_renewal_date_page(self) -> bool:
        logger.info(f"Navigating to renewal page for {self.line.name}.")

        try:
            self.driver.get("https://my.te.eg/echannel/#/overview")
            _renewal_cost_selector = "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-xs-24.ant-col-sm-24.ant-col-md-14.ant-col-lg-14.ant-col-xl-14 > div > div > div > div > div:nth-child(3) > div > span:nth-child(2) > div > div:nth-child(1)"
            _renewal_date_selector = "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-xs-24.ant-col-sm-24.ant-col-md-14.ant-col-lg-14.ant-col-xl-14 > div > div > div > div > div:nth-child(4) > div > span"

            await WebDriverWait(self.driver, 7).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, _renewal_cost_selector)
                )
            )
            await asyncio.sleep(2)
            logger.debug(
                f"Renewal page loaded successfully for {self.line.name}."
            )

            # Extracting renewal cost and date
            self.renewal_cost = float(
                self.driver.find_element(
                    By.CSS_SELECTOR, _renewal_cost_selector
                ).text.replace(",", "")
            )
            renewal_date_element = self.driver.find_element(
                By.CSS_SELECTOR, _renewal_date_selector
            ).text
            await self._set_renewal_date(renewal_date_element)
            logger.info(
                f"Extracted renewal cost and date for {self.line.name} - Renewal Cost: {
                    self.renewal_cost}, Renewal Date: {self.renewal_date}, Remaining Days: {self.remaining_days}",
            )
            self.succeed = True
            return True
        except Exception as e:
            logger.error(
                f"Error extracting renewal page for {
                         self.line.name}: {e}"
            )
            return False

    async def _set_renewal_date(self, renewal_date_element: str):
        logger.debug(f"Setting renewal date for {self.line.name}.")
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
                f"Error setting renewal date for {
                         self.line.name}: {e}"
            )

    async def _calc_usage_percentage(
        self, used: float, remaining: float
    ) -> float:
        try:
            total = used + remaining
            return int((used / total) * 100)
        except ZeroDivisionError:
            logger.error(
                f"Division by zero error for {self.line.name}. Used: {
                    used}, Remaining: {remaining}",
            )
            return 0.0
