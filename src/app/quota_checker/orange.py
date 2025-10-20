import asyncio
import logging
import re
from datetime import datetime
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium_async import Options, launch

from app.wait import WebDriverWait
from core.scraper_config import orange_selectors, timeouts
from db.model import Line, QuotaResult

logger = logging.getLogger(__name__)


class OrangeWebScraper:
    """Orange Egypt Scraping Class"""

    failed_list = []

    def __init__(
        self,
        line: Line,
        headless: Optional[bool] = False,
    ) -> None:
        """Initialize with line details and headless option"""
        self.line = line
        self.headless = headless

        # Parsed values
        self.balance = None
        self.expiry_date = None
        self.total_consumption = None
        self.remaining = None
        self.used = None
        self.renewal_date = None
        self.remaining_days = None
        self.used_perc = None
        self.succeed = False

    async def __aenter__(self):
        logger.info(f"Launching browser for {self.line.name}")
        self.driver = await launch(options=Options(headless=self.headless))
        return self

    async def __aexit__(self, *args, **kwargs):
        logger.info(f"Closing browser for {self.line.name}")
        if self.driver:
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
            renewal_cost=None,  # Not available for Orange
        )

    async def login(self) -> bool:
        try:
            logger.info(f"Logging in for {self.line.name}")
            self.driver.get("https://www.orange.eg/ar/myaccount/login")

            # Wait for dial number input to be present
            await WebDriverWait(self.driver, timeouts.login_wait).until(
                EC.presence_of_element_located(
                    (By.ID, orange_selectors.login_dial_number)
                )
            )

            # Input dial number
            dial_number_input = self.driver.find_element(
                By.ID, orange_selectors.login_dial_number
            )
            dial_number_input.click()
            dial_number_input.send_keys(self.line.portal_username)

            # Dispatch input and change events using JavaScript
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));"
                "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                dial_number_input,
            )

            # Input password
            password_input = self.driver.find_element(
                By.ID, orange_selectors.login_password
            )
            password_input.click()
            password_input.send_keys(self.line.get_password())

            # Dispatch input and change events using JavaScript
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));"
                "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                password_input,
            )

            # Wait briefly for button to potentially enable
            await asyncio.sleep(0.2)

            # Click login button
            login_button = self.driver.find_element(
                By.ID, orange_selectors.login_button
            )

            if login_button.is_enabled():
                login_button.click()
                await asyncio.sleep(timeouts.post_action_delay)
                logger.info(f"{self.line.name} logged in successfully")
                return True
            else:
                logger.warning(
                    f"Login button is disabled for {self.line.name}"
                )
                return False

        except Exception as e:
            logger.error(f"Login failed for {self.line.name}: {e}")
            return False

    async def scrap_balance_page(self) -> bool:
        """Scrape balance and expiry date from account overview"""
        logger.info(f"Navigating to balance page for {self.line.name}")

        try:
            self.driver.get("https://www.orange.eg/ar/myaccount/")

            await WebDriverWait(self.driver, timeouts.page_load_wait).until(
                EC.presence_of_element_located(
                    (By.ID, orange_selectors.balance_container)
                )
            )
            await asyncio.sleep(timeouts.element_wait)
            logger.debug(
                f"Balance page loaded successfully for {self.line.name}"
            )

            # Extract balance
            balance_container = self.driver.find_element(
                By.ID, orange_selectors.balance_container
            )
            raw_balance_text = balance_container.text.strip()
            balance_match = re.search(r"\d+", raw_balance_text)
            self.balance = (
                float(balance_match.group(0)) if balance_match else None
            )

            # Extract expiry date
            expiry_container = self.driver.find_element(
                By.ID, orange_selectors.expiry_date_container
            )
            raw_expiry_text = expiry_container.text.strip()
            # Remove "صالح حتى" (valid until) prefix
            self.expiry_date = re.sub(
                r"^صالح حتى\s*", "", raw_expiry_text, flags=re.IGNORECASE
            ).strip()

            logger.info(
                f"Extracted balance for {self.line.name} - Balance: {self.balance}, Expiry: {self.expiry_date}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error extracting balance page for {self.line.name}: {e}"
            )
            return False

    async def scrap_internet_page(self) -> bool:
        """Scrape internet consumption data"""
        logger.info(f"Navigating to internet page for {self.line.name}")

        try:
            self.driver.get("https://www.orange.eg/ar/myaccount/internet")

            await WebDriverWait(self.driver, timeouts.page_load_wait).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, orange_selectors.total_consumption)
                )
            )
            await asyncio.sleep(timeouts.element_wait)
            logger.debug(
                f"Internet page loaded successfully for {self.line.name}"
            )

            # Extract total consumption
            total_elem = self.driver.find_element(
                By.CSS_SELECTOR, orange_selectors.total_consumption
            )
            raw_total = total_elem.text.strip()
            self.total_consumption = float(
                re.sub(r"GB", "", raw_total, flags=re.IGNORECASE).strip()
            )

            # Extract remaining (in MB, convert to GB)
            remaining_elem = self.driver.find_element(
                By.CSS_SELECTOR, orange_selectors.data_remaining
            )
            remaining_mb_text = remaining_elem.text.strip()
            remaining_mb = float(
                re.sub(
                    r"MBs?", "", remaining_mb_text, flags=re.IGNORECASE
                ).strip()
            )
            self.remaining = remaining_mb / 1000  # Convert to GB

            # Calculate used
            self.used = self.total_consumption - self.remaining

            # Calculate usage percentage
            self.used_perc = await self._calc_used_perc(
                self.used, self.remaining
            )

            # Extract renewal date
            renewal_elem = self.driver.find_element(
                By.CSS_SELECTOR, orange_selectors.renewal_date
            )
            self.renewal_date = renewal_elem.text.strip()

            # Calculate remaining days
            self.remaining_days = await self._calc_remaining_days(
                self.renewal_date
            )

            logger.info(
                f"Extracted internet data for {self.line.name} - Total: {self.total_consumption}GB, "
                f"Used: {self.used}GB, Remaining: {self.remaining}GB, Usage: {self.used_perc}%, "
                f"Renewal: {self.renewal_date}, Remaining Days: {self.remaining_days}"
            )
            self.succeed = True
            return True

        except Exception as e:
            logger.error(
                f"Error extracting internet page for {self.line.name}: {e}"
            )
            return False

    async def _calc_used_perc(self, used: float, remaining: float) -> float:
        """Calculate usage percentage"""
        try:
            total = used + remaining
            return round((used / total) * 100, 2) if total > 0 else 0.0
        except ZeroDivisionError:
            logger.error(
                f"Division by zero error for {self.line.name}. Used: {used}, Remaining: {remaining}"
            )
            return 0.0

    async def _calc_remaining_days(self, date_str: str) -> int:
        """Calculate remaining days from Arabic date string"""
        try:
            # Arabic month mapping
            arabic_months = {
                "يناير": 1,
                "فبراير": 2,
                "مارس": 3,
                "أبريل": 4,
                "مايو": 5,
                "يونيو": 6,
                "يوليو": 7,
                "أغسطس": 8,
                "سبتمبر": 9,
                "أكتوبر": 10,
                "نوفمبر": 11,
                "ديسمبر": 12,
            }

            # Parse date string (e.g., "22 أكتوبر 2025")
            parts = date_str.split()
            day = int(parts[0])
            month = arabic_months.get(parts[1], 1)
            year = int(parts[2])

            # Create target date
            target_date = datetime(year, month, day)
            today = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            # Calculate difference
            diff = (target_date - today).days
            return max(0, diff)  # Return 0 if negative

        except Exception as e:
            logger.error(
                f"Error calculating remaining days for {self.line.name}: {e}"
            )
            return 0
