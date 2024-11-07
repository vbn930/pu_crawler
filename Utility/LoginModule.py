import sys
sys.path.append("./Utility")
from Utility import Util

from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip
import time

def pu_login_module(driver_manager, logger, number, id, pw):
    try:
        driver = driver_manager.get_driver()
        login_url = "https://dealer.parts-unlimited.com/login"
        if driver is None:
            return False
        
        if driver.current_url is not login_url:
            driver_manager.get_page(login_url)

        number_input = driver.find_element(By.NAME, "dealerCode").send_keys(number)
        # number_input.click()
        # pyperclip.copy(number)
        # actions = ActionChains(driver)
        # actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        Util.wait_time(logger, 2)
        driver.get_screenshot_as_file("number_input.png")
            
        id_input = driver.find_element(By.NAME, "username").send_keys(id)
        # id_input.click()
        # pyperclip.copy(id)
        # actions = ActionChains(driver)
        # actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        Util.wait_time(logger, 2)
        driver.get_screenshot_as_file("id_input.png")

        pw_input = driver.find_element(By.NAME, "password").send_keys(pw)
        # pw_input.click()
        # pyperclip.copy(pw)
        # actions = ActionChains(driver)
        # actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        Util.wait_time(logger, 2)
        driver.get_screenshot_as_file("pw_input.png")

        driver.find_element(By.CLASS_NAME, "btn.btn-secondary").click()
        Util.wait_time(logger, 5)
        
        if driver.current_url == login_url:
            driver_manager.logger.log(log_level="Error", log_msg="Login failed! Check your account again")
            return False
        driver_manager.logger.log(log_level="Event", log_msg="Login succes!")
        return True
    except Exception as e:
        self.logger.log(log_level="Error", log_msg=f"Error in login module {e}")
        return False
