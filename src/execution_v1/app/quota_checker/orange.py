import asyncio
import re
import uuid
from typing import Optional

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium_async import Options, launch

from app.logger import logger
from app.wait import WebDriverWait
from db.model import Line, QuotaResult


# WEWebScraper class
class OrangeScrapper:
    """WE Scraping Base Class"""

    failed_list = []

    def __init__(
        self,
        line: Line,
        headless: Optional[bool] = False,
    ) -> None:
        """Initialize with line details and headless option"""
        self.pid = str(uuid.uuid4())  # Generate a unique process ID
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
        await logger.info(self.pid, f"Launching browser for {self.line.name}.")
        self.driver = await launch(options=Options(headless=self.headless))
        return self

    async def __aexit__(self, *args, **kwargs):
        await logger.info(self.pid, f"Closing browser for {self.line.name}.")
        self.driver.quit()
        if not self.succeed:
            await logger.warning(
                self.pid, f"Scraping failed for {self.line.name}."
            )
            if self.line not in self.failed_list:
                self.failed_list.append(self.line)
        self.result = QuotaResult(
            line_id=self.line.id,
            process_id=self.pid,
            data_used=self.used,
            usage_percentage=self.used_perc,
            data_remaining=self.remaining,
            balance=self.balance,
            renewal_date=self.renewal_date,
            remaining_days=self.remaining_days,
            renewal_cost=self.renewal_cost,
        )

    async def login(self) -> bool:
        """
        Logs into Orange Egypt portal using credentials from self.line.
        Returns True if login successful, False otherwise.
        """
        try:
            await logger.info(self.pid, f"Logging in for {self.line.name}.")

            # Navigate to Orange Egypt portal
            self.driver.get("https://www.orange.eg/ar/")

            # Set window size for consistent element visibility
            self.driver.set_window_size(1382, 744)

            # Wait for and click "Sign In" button
            await WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.ID, "GSM_Portal_TopHeader_lblSignIn")
                )
            )
            self.driver.find_element(
                By.ID, "GSM_Portal_TopHeader_lblSignIn"
            ).click()

            # Wait for login form to appear
            await WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.ID, "PlaceHolderAppsHP_LoginControl_txtDialNumber")
                )
            )

            # Input phone number (username)
            phone_input = self.driver.find_element(
                By.ID, "PlaceHolderAppsHP_LoginControl_txtDialNumber"
            )
            phone_input.click()
            phone_input.clear()
            phone_input.send_keys(self.line.portal_username)

            # Wait briefly for any auto-complete/validation
            await asyncio.sleep(0.3)

            # Input password
            password_input = self.driver.find_element(
                By.ID, "PlaceHolderAppsHP_LoginControl_txtPassword"
            )
            password_input.click()
            password_input.clear()
            password_input.send_keys(self.line.portal_password)

            # Submit form by pressing Enter
            password_input.send_keys(Keys.ENTER)

            # Wait for login to complete (adjust timeout as needed)
            await asyncio.sleep(1.5)

            # Verify successful login by checking for logged-in state indicator
            # (adjust selector based on what appears after successful login)
            try:
                await WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (
                            By.ID,
                            "GSM_Portal_TopHeader_lblSignOut",
                        )  # Or another post-login element
                    )
                )
                await logger.info(
                    self.pid, f"{self.line.name} logged in successfully."
                )
                return True
            except:
                # Check if we're still on login page (login failed)
                if (
                    "PlaceHolderAppsHP_LoginControl_txtDialNumber"
                    in self.driver.page_source
                ):
                    await logger.error(
                        self.pid,
                        f"Login failed for {self.line.name}: Still on login page",
                    )
                    return False
                # Assume success if we're not on login page
                await logger.info(
                    self.pid, f"{self.line.name} logged in successfully."
                )
                return True

        except TimeoutException as e:
            await logger.error(
                self.pid,
                f"Login timeout for {self.line.name}: Element not found - {e}",
            )
            return False
        except NoSuchElementException as e:
            await logger.error(
                self.pid,
                f"Login failed for {self.line.name}: Element not found - {e}",
            )
            return False
        except Exception as e:
            await logger.error(
                self.pid, f"Login failed for {self.line.name}: {e}"
            )
            return False

    async def scrap_overview_page(self) -> bool:
        await logger.info(
            self.pid, f"Navigating to overview page for {self.line.name}."
        )
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
            await logger.debug(
                self.pid,
                f"Overview page loaded successfully for {self.line.name}.",
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
            self.used_perc = await self._calc_used_perc(
                self.used, self.remaining
            )

            await logger.info(
                self.pid,
                f"Extracted values for {self.line.name} - Balance: {self.balance}, Used: {self.used}, Remaining: {self.remaining}, Usage Percentage: {self.used_perc}%",
            )
            self.succeed = True
            return True
        except Exception as e:
            await logger.error(
                self.pid,
                f"Error extracting overview page for {self.line.name}: {e}",
            )
            return False

    async def scrap_renewaldate_page(self) -> bool:
        await logger.info(
            self.pid, f"Navigating to renewal page for {self.line.name}."
        )

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
            await logger.debug(
                self.pid,
                f"Renewal page loaded successfully for {self.line.name}.",
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

            await logger.info(
                self.pid,
                f"Extracted renewal cost and date for {self.line.name} - Renewal Cost: {self.renewal_cost}, Renewal Date: {self.renewal_date}, Remaining Days: {self.remaining_days}",
            )
            self.succeed = True
            return True
        except Exception as e:
            await logger.error(
                self.pid,
                f"Error extracting renewal page for {self.line.name}: {e}",
            )
            return False

    async def _set_renewal_date(self, renewal_date_element: str):
        await logger.debug(
            self.pid, f"Setting renewal date for {self.line.name}."
        )
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
            await logger.error(
                self.pid,
                f"Error setting renewal date for {self.line.name}: {e}",
            )

    async def _calc_used_perc(self, used: float, remaining: float) -> float:
        try:
            total = used + remaining
            return (used / total) * 100
        except ZeroDivisionError:
            await logger.error(
                self.pid,
                f"Division by zero error for {self.line.name}. Used: {used}, Remaining: {remaining}",
            )
            return 0.0
