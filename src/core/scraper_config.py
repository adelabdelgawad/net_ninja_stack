# core/scraper_config.py
from pydantic import BaseModel


class ScraperTimeouts(BaseModel):
    """Timeout configurations for web scraping (shared across all ISPs)"""

    login_wait: int = 5
    page_load_wait: int = 7
    element_wait: int = 2
    post_action_delay: float = 0.5


class OrangeScraperSelectors(BaseModel):
    """CSS selectors for Orange Egypt portal"""

    # Login page selectors
    login_dial_number: str = "PlaceHolderAppsHP_LoginControl_txtDialNumber"
    login_password: str = "PlaceHolderAppsHP_LoginControl_txtPassword"
    login_button: str = "GSM_Portal_Login_btnLogin"

    # Balance page selectors
    balance_container: str = "BillAndBalanceInfo1_divContolCurrentBalance"
    expiry_date_container: str = "BillAndBalanceInfo1_divControlExpiryDate"

    # Internet consumption page selectors
    total_consumption: str = ".total-consumption"
    data_remaining: str = (
        "#MainContMiddle > div > div:nth-child(2) > app-root > div > app-internet-consumption > div > app-main-bucket-consumption > section > div.main-package__consumption > div.row.justify-content-between.g-0 > div:nth-child(1) > p:nth-child(1) > span.orange"
    )
    renewal_date: str = (
        "#MainContMiddle > div > div:nth-child(2) > app-root > div > app-internet-consumption > div > app-main-bucket-consumption > section > div.main-package__consumption > div.row.justify-content-between.g-0 > div:nth-child(1) > p:nth-child(2) > span.orange"
    )


class WEScraperSelectors(BaseModel):
    """CSS selectors for WE (Telecom Egypt) portal"""

    # Login page selectors
    login_id: str = "login_loginid_input_01"
    login_type: str = "login_input_type_01"
    login_password: str = "login_password_input_01"
    login_button: str = "login-withecare"
    account_type_selector: str = (
        ".ant-select-item-option-active .ant-space-item:nth-child(2) > span"
    )

    # Overview page selectors
    balance: str = (
        "#_bes_window > main > div > div > div.ant-row > div:nth-child(2) > div > div > div > div > div:nth-child(3) > div:nth-child(1)"
    )
    data_used: str = (
        "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-24 > div > div > div.ant-row.ec_accountoverview_primaryBtn_Qyg-Vp > div:nth-child(2) > div > div > div.slick-list > div > div.slick-slide.slick-active.slick-current > div > div > div > div > div:nth-child(2) > div:nth-child(2) > span:nth-child(1)"
    )
    data_remaining: str = (
        "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-24 > div > div > div.ant-row.ec_accountoverview_primaryBtn_Qyg-Vp > div:nth-child(2) > div > div > div.slick-list > div > div.slick-slide.slick-active.slick-current > div > div > div > div > div:nth-child(2) > div:nth-child(1) > span:nth-child(1)"
    )

    # Renewal page selectors
    renewal_cost: str = (
        "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-xs-24.ant-col-sm-24.ant-col-md-14.ant-col-lg-14.ant-col-xl-14 > div > div > div > div > div:nth-child(3) > div > span:nth-child(2) > div > div:nth-child(1)"
    )
    renewal_date: str = (
        "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-xs-24.ant-col-sm-24.ant-col-md-14.ant-col-lg-14.ant-col-xl-14 > div > div > div > div > div:nth-child(4) > div > span"
    )


# Shared timeout configuration
timeouts = ScraperTimeouts()

# WE-specific selectors
we_selectors = WEScraperSelectors()
orange_selectors = OrangeScraperSelectors()
