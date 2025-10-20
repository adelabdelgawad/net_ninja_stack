from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


class TestTt:
    def setup_method(self, method):
        self.driver = webdriver.Firefox()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_tt(self):
        # Test name: tt
        # Step # | name | target | value
        # 1 | open | /ar/ |
        self.driver.get("https://www.orange.eg/ar/")
        # 2 | setWindowSize | 1382x744 |
        self.driver.set_window_size(1382, 744)
        # 3 | click | id=GSM_Portal_TopHeader_lblSignIn |
        self.driver.find_element(
            By.ID, "GSM_Portal_TopHeader_lblSignIn"
        ).click()
        # 4 | click | id=PlaceHolderAppsHP_LoginControl_txtDialNumber |
        self.driver.find_element(
            By.ID, "PlaceHolderAppsHP_LoginControl_txtDialNumber"
        ).click()
        # 5 | type | id=PlaceHolderAppsHP_LoginControl_txtDialNumber | 01274629814
        self.driver.find_element(
            By.ID, "PlaceHolderAppsHP_LoginControl_txtDialNumber"
        ).send_keys("01274629814")
        # 6 | click | id=PlaceHolderAppsHP_LoginControl_txtPassword |
        self.driver.find_element(
            By.ID, "PlaceHolderAppsHP_LoginControl_txtPassword"
        ).click()
        # 7 | type | id=PlaceHolderAppsHP_LoginControl_txtPassword | @Ndalusiasoft2115
        self.driver.find_element(
            By.ID, "PlaceHolderAppsHP_LoginControl_txtPassword"
        ).send_keys("@Ndalusiasoft2115")
        # 8 | sendKeys | id=PlaceHolderAppsHP_LoginControl_txtPassword | ${KEY_ENTER}
        self.driver.find_element(
            By.ID, "PlaceHolderAppsHP_LoginControl_txtPassword"
        ).send_keys(Keys.ENTER)
        # 9 | click | id=TopHeader_spanAnonymousIcon |
        self.driver.find_element(By.ID, "TopHeader_spanAnonymousIcon").click()
        # 10 | click | id=TopHeader_lnkMyAccount |
        self.driver.find_element(By.ID, "TopHeader_lnkMyAccount").click()
        # 11 | click | id=MyInternet1_lnkABSCorporate |
        self.driver.find_element(By.ID, "MyInternet1_lnkABSCorporate").click()
        # 12 | click | css=.ng-input > input |
        self.driver.find_element(By.CSS_SELECTOR, ".ng-input > input").click()
        # 13 | click | css=.ng-input > input |
        self.driver.find_element(By.CSS_SELECTOR, ".ng-input > input").click()
        # 14 | click | css=app-root > .mb-4:nth-child(3) > p |
        self.driver.find_element(
            By.CSS_SELECTOR, "app-root > .mb-4:nth-child(3) > p"
        ).click()
        # 15 | click | css=span:nth-child(2) > .BreadCLink > span |
        self.driver.find_element(
            By.CSS_SELECTOR, "span:nth-child(2) > .BreadCLink > span"
        ).click()
        # 16 | runScript | window.scrollTo(0,2) |
        self.driver.execute_script("window.scrollTo(0,2)")
        # 17 | click | id=MyInternet1_lnkOnlineBucketAction |
        self.driver.find_element(
            By.ID, "MyInternet1_lnkOnlineBucketAction"
        ).click()
        # 18 | click | css=.main-package__consumption |
        self.driver.find_element(
            By.CSS_SELECTOR, ".main-package__consumption"
        ).click()
        # 19 | click | css=.m-0:nth-child(1) > .orange |
        self.driver.find_element(
            By.CSS_SELECTOR, ".m-0:nth-child(1) > .orange"
        ).click()
        # 20 | click | css=.m-0:nth-child(2) > .orange |
        self.driver.find_element(
            By.CSS_SELECTOR, ".m-0:nth-child(2) > .orange"
        ).click()
        # 21 | click | css=.m-0:nth-child(2) > .orange |
        self.driver.find_element(
            By.CSS_SELECTOR, ".m-0:nth-child(2) > .orange"
        ).click()
        # 22 | doubleClick | css=.m-0:nth-child(2) > .orange |
        element = self.driver.find_element(
            By.CSS_SELECTOR, ".m-0:nth-child(2) > .orange"
        )
        actions = ActionChains(self.driver)
        actions.double_click(element).perform()
        # 23 | click | css=.m-0:nth-child(2) |
        self.driver.find_element(By.CSS_SELECTOR, ".m-0:nth-child(2)").click()
        # 24 | click | css=#OrangeContainer > div:nth-child(2) |
        self.driver.find_element(
            By.CSS_SELECTOR, "#OrangeContainer > div:nth-child(2)"
        ).click()
