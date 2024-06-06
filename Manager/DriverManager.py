import sys
sys.path.append("./Utility")
from Utility import Util

import undetected_chromedriver as uc 
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium_stealth import stealth
import pyperclip
import subprocess
import time
from datetime import datetime
import requests
import os
import psutil
from PIL import Image

class WebDriverManager:
    def __init__(self, logger, is_headless=False):
        self.logger = logger
        self.is_headless = is_headless
        self.logger.log(log_level="Debug", log_msg="Driver init")
        self.driver = None
        self.open_driver()
        self.process_list = []
        for proc in psutil.process_iter():
            # 프로세스 이름을 ps_name에 할당
            ps_name = proc.name()
            if ps_name == "chrome.exe":
                self.process_list.append(proc.pid)


    def open_driver(self):
        options = uc.ChromeOptions() 
        options.headless = True  # Set headless to False to run in non-headless mode
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-notifications")
        driver = uc.Chrome(use_subprocess=True, options=options) 
        #driver.maximize_window()
        if self.is_headless == True: 
            driver.minimize_window()
    
        self.driver = driver
        self.driver.set_page_load_timeout(10)
    
    def close_driver(self):
        if self.driver != None:
            pid = self.driver.service.process.pid
            self.driver.quit()
            self.logger.log(log_level="Debug", log_msg=f"Driver PID : {pid}")
            new_process_list = []
            for proc in psutil.process_iter():
                # 프로세스 이름을 ps_name에 할당
                ps_name = proc.name()
                if ps_name == "chrome.exe":
                    new_process_list.append(proc.pid)
            new_process_list = list(set(new_process_list) - set(self.process_list))
            self.logger.log(log_level="Debug", log_msg=f"New pid : {new_process_list}")
            for p in new_process_list:
                os.system("taskkill /pid {} /t".format(pid))
                self.logger.log(log_level="Debug", log_msg=f"Kill pid {pid}")
            self.driver = None
            self.logger.log(log_level="Debug", log_msg=f"Driver deleted")

    def get_page(self, url, max_wait_time = 10):
        is_page_loaded = False
        while(is_page_loaded == False):
            try:
                self.driver.get(url)
                self.driver.implicitly_wait(max_wait_time)
                self.logger.log(log_level="Debug", log_msg=f"Get *{url}* page")
                self.driver.get_screenshot_as_file("temp.png")
                is_page_loaded = True
            except:
                self.logger.log(log_level="Debug", log_msg=f"Page load failed")
                is_page_loaded = False
            if self.is_headless == True: 
                self.driver.minimize_window()

    def get_driver(self):
        return self.driver

    def is_element_exist(self, find_type, element):
        is_exist = False
        try:
            self.driver.find_element(find_type, element)
            is_exist = True
        except NoSuchElementException:
            is_exist = False
        return is_exist

    def download_image(self, img_url, img_name, img_path, download_cnt):
        min_size = 50
        
        #만약 다운로드 시도횟수가 5번을 넘는다면 다운로드 불가능한 이미지로 간주
        if download_cnt > 5:
            self.logger.log(log_level="Error", log_msg=f"Img size is under {min_size}KB or cannot download image \'{img_name}\'")
            return
        r = requests.get(img_url,headers={'User-Agent': 'Mozilla/5.0'})
        with open(f"{img_path}/{img_name}.png", "wb") as outfile:
            outfile.write(r.content)
        #KB 단위의 이미지 사이즈
        img_size = os.path.getsize(f"{img_path}/{img_name}.png") / 1024

        #만약 이미지 크기가 일정 크기 이하라면 다운로드가 실패한것으로 간주, 다시 다운로드
        if img_size < min_size:
            self.logger.log(log_level="Debug", log_msg=f"Image \'{img_name}\' download failed")
            self.download_image(img_url, img_name, img_path, download_cnt + 1)
        else:
            self.logger.log(log_level="Debug", log_msg=f"Image \'{img_name}\' download completed")
        return

    def __del__(self):
        self.close_driver()