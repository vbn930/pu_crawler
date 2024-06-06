from Utility import Util
from Manager import DriverManager
from Utility import LoginModule
from Manager import FileManager

from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from dataclasses import dataclass
import pandas as pd
import datetime


@dataclass
class ProductInfo:
    name: str
    spec_name: str
    your_price: str
    suggested_price: str
    product_number: str
    product_code: str
    product_abbreviation: str
    description: str
    trans_description: str
    fitments: list
    images: list

class PU_Crawler:
    def __init__(self, logger):
        self.file_manager = FileManager.FileManager()
        self.logger = logger
        self.driver_manager = DriverManager.WebDriverManager(self.logger, False)
        self.driver = self.driver_manager.driver
        self.file_manager.creat_dir("./temp")
        self.file_manager.creat_dir("./output")
        self.product_numbers = []
        self.product_abbreviations = []
        self.account = []
        self.product_informations = []
        self.data = dict()
        self.data_init()

    def data_init(self):
        self.data.clear()
        self.data["PU 품번"] = list()
        self.data["제조사 품번"] = list()
        self.data["자체 품번"] = list()
        self.data["상품명"] = list()
        self.data["상품명 상세"] = list()
        self.data["설명"] = list()
        self.data["설명 번역"] = list()
        self.data["YOUR PRICE"] = list()
        self.data["SUGGESTED RETAIL"] = list()
        self.data["대표 이미지"] = list()
        self.data["상세 이미지"] = list()
        self.data["Fitments-year"] = list()
        self.data["Fitments-make"] = list()
        self.data["Fitments-model"] = list()
        self.data["Fitments-position"] = list()
        self.data["Fitments-notes"] = list()

    def product_info_factory(self, name, spec_name, your_price, suggested_price, product_number, product_code, product_abbreviation, description, fitments, images):
        trans_description = Util.translator("en", "ko", description)
        info = ProductInfo(name=name, spec_name=spec_name, your_price=your_price, suggested_price=suggested_price, product_number=product_number,
        product_code=product_code, product_abbreviation=product_abbreviation, description=description, trans_description=trans_description, fitments=fitments, images=images)
        return info
    
    def product_info_to_csv_data(self, product_info: ProductInfo):
        self.data["PU 품번"].append(product_info.product_number)
        self.data["제조사 품번"].append(product_info.product_code)
        company_code = f"{product_info.product_abbreviation}-{product_info.product_code}"
        self.data["자체 품번"].append(company_code)
        self.data["상품명"].append(product_info.name)
        self.data["상품명 상세"].append(product_info.spec_name)
        self.data["설명"].append(product_info.description)
        self.data["설명 번역"].append(product_info.trans_description)

        your_price = product_info.your_price.replace(",", "")
        your_price = your_price.replace("$", "")
        if your_price == "":
            self.data["YOUR PRICE"].append(your_price)
        else:
            self.data["YOUR PRICE"].append(float(your_price))
        
        suggested_price = product_info.suggested_price.replace(",", "")
        suggested_price = suggested_price.replace("$", "")
        if suggested_price == "":
            self.data["SUGGESTED RETAIL"].append(suggested_price)
        else:
            self.data["SUGGESTED RETAIL"].append(float(suggested_price))
        if len(product_info.images) != 0:
            self.data["대표 이미지"].append(product_info.images[0])

            #이미지 이름들 한줄로 포멧팅
            imgs = ""
            for img in product_info.images:
                imgs += img
                if img != product_info.images[-1]:
                    imgs += "|"

            self.data["상세 이미지"].append(imgs)
        else:
            self.data["대표 이미지"].append("")
            self.data["상세 이미지"].append("")
        self.data["Fitments-year"].append(product_info.fitments[0].replace("\n", "|"))
        self.data["Fitments-make"].append(product_info.fitments[1].replace("\n", "|"))
        self.data["Fitments-model"].append(product_info.fitments[2].replace("\n", "|"))
        self.data["Fitments-position"].append(product_info.fitments[3].replace("\n", "|"))
        self.data["Fitments-notes"].append(product_info.fitments[4].replace("\n", "|"))
        return

    def fill_empty_data_to_csv(self, product_number):
        empty_data = ""
        self.data["PU 품번"].append(product_number)
        self.data["제조사 품번"].append(empty_data)
        self.data["자체 품번"].append(empty_data)
        self.data["상품명"].append(empty_data)
        self.data["상품명 상세"].append(empty_data)
        self.data["설명"].append(empty_data)
        self.data["설명 번역"].append(empty_data)
        self.data["YOUR PRICE"].append(empty_data)
        self.data["SUGGESTED RETAIL"].append(empty_data)
        self.data["대표 이미지"].append(empty_data)
        self.data["상세 이미지"].append(empty_data)
        self.data["Fitments-year"].append(empty_data)
        self.data["Fitments-make"].append(empty_data)
        self.data["Fitments-model"].append(empty_data)
        self.data["Fitments-position"].append(empty_data)
        self.data["Fitments-notes"].append(empty_data)

    def save_csv_datas(self, dir_path, file_name):
        for product_info in self.product_informations:
            if isinstance(product_info, ProductInfo) != True:
                self.fill_empty_data_to_csv(product_info)
            else:
                self.product_info_to_csv_data(product_info)
        data_frame = pd.DataFrame(self.data)
        data_frame.to_excel(f"{dir_path}/{file_name}.xlsx", index=False)
        return
    
    def get_settings(self):
        #cvs 파일에서 계정 정보, 브랜드, 브랜드 코드 가져오기
        data = pd.read_csv("./setting.csv").fillna(0)
        product_numbers = data["product_number"].to_list()
        product_numbers.append(0)
        product_numbers = product_numbers[0:product_numbers.index(0)]
        product_abbreviations = data["product_abbreviation"].to_list()
        product_abbreviations.append(0)
        product_abbreviations = product_abbreviations[0:product_abbreviations.index(0)]
        account = data["account"].to_list()
        account.append(0)
        account = account[0:account.index(0)]

        self.product_numbers = product_numbers
        self.product_abbreviations = product_abbreviations
        self.account = account

    def login(self):
        number = self.account[0]
        id = self.account[1]
        pw = self.account[2]

        self.logger.log(log_level="Event", log_msg="PU crawler")
        self.logger.log(log_level="Event", log_msg=f"Dealer Number : {number}, ID : {id}, PW : {pw}")

        if LoginModule.pu_login_module(self.driver_manager, self.logger, number, id, pw):
            return True
        return False
    
    def set_show_dealer_price(self):
        menu_btn = self.driver.find_element(By.ID, "loginNavbarDropdown")
        menu_btn.click()
        Util.wait_time(self.logger, 2)
        toggle_switch = self.driver.find_element(By.CLASS_NAME, "custom-control.custom-switch.custom-switch-light")
        toggle_switch.click()
        Util.wait_time(self.logger, 2)
        return True

    def search_product(self, product_number, max_retry_count):
        replace_str = product_number.replace("/","%2F")
        search_url = f"https://dealer.parts-unlimited.com/search;q={replace_str}"
        product_urls = []
        self.driver_manager.get_page(search_url)
        if self.driver_manager.is_element_exist(By.CLASS_NAME, "card.part-badge.part-badge-grid.p-2.pt-4.SEARCH.ng-star-inserted"):
            product_elemnets = self.driver.find_elements(By.CLASS_NAME, "card.part-badge.part-badge-grid.p-2.pt-4.SEARCH.ng-star-inserted")
            for product_elemnet in product_elemnets:
                product_url = self.driver.find_element(By.CLASS_NAME, "text-dark.text-decoration-none").get_attribute("href")
                product_urls.append(product_url)
                self.logger.log(log_level="Debug", log_msg=f"Find product code {product_number} : {product_url}")
        else:
            self.logger.log(log_level="Error", log_msg=f"Can not find product code {product_number}") 
            max_retry_count += 1
        return product_urls

    def get_product_info(self, product_number, product_abbreviation, product_url, output_name):
        #Fitments가 여러개라면 Fitments만 다르게 같은 상품을 여러개 반환해야함
        product_infos = []
        self.driver_manager.get_page(product_url)
        product_info_elements = self.driver.find_element(By.CLASS_NAME, "pl-0.middot-list.mb-0").find_elements(By.TAG_NAME, "li")
        if len(product_info_elements) < 3:
            product_number = product_number
            product_code = product_info_elements[0].text
            product_name = product_info_elements[1].text
        else:
            product_number = product_info_elements[0].text
            product_code = product_info_elements[1].text
            product_name = product_info_elements[2].text
        product_spec_name = self.driver.find_element(By.CLASS_NAME, "font-weight-light.text-muted.h5.ng-star-inserted").text

        #가격 크롤링
        price = []
        your_price = ""
        suggested_price = ""

        if self.driver_manager.is_element_exist(By.CLASS_NAME, "col-6.col-md-5"):
            price_elements = self.driver.find_elements(By.CLASS_NAME, "col-6.col-md-5")
            for price_element in price_elements:
                text = price_element.text.split("\n")
                if len(text) == 1:
                    price.append("")
                elif text[1] == "N/A":
                    price.append("")
                else:
                    text = price_element.text.split("\n")[1]
                    price.append(text)
            your_price = price[0]
            suggested_price = price[1]
        else:
            your_price = ""
            suggested_price = ""

        #상품 설명 크롤링
        features = ""
        if self.driver_manager.is_element_exist(By.CLASS_NAME, "col.mb-3.mb-md-4.ng-star-inserted"):
            text_elements = self.driver.find_element(By.CLASS_NAME, "col.mb-3.mb-md-4.ng-star-inserted").find_elements(By.TAG_NAME, "li")
            for text_element in text_elements:
                text = text_element.text
                features += text
                if text_element != text_elements[-1]:
                    features += "|"
        
        #Fitments 크롤링
        fitments = []
        if self.driver_manager.is_element_exist(By.TAG_NAME, "ecfe-fitments-table"):
            table_rows = self.driver.find_element(By.TAG_NAME, "ecfe-fitments-table").find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
            for table_row in table_rows:
                fitment = []
                row_elements = table_row.find_elements(By.TAG_NAME, "td")
                for row_element in row_elements:
                    text = row_element.text
                    fitment.append(text)
                fitments.append(fitment)
        
        if len(fitments) == 0:
            fitments.append(["", "", "", "", ""])
        
        #이미지 크롤링 (제일 마지막에 해야함 -> 페이지를 이동하기 때문)
        # 상품 이미지 링크 규칙
        # src="https://asset.parts-unlimited.com/media/4f5c7a4e-b53e-4a05-92b6-fe5477c565aa.png?x=120&y=120&b=&t=image/jpeg" 여기서 ? 를 기준으로 뒤를 날리면 원본이미지 링크 나옴
        img_srcs = []
        if self.driver_manager.is_element_exist(By.CLASS_NAME, "four-per-row"):
            #상세 이미지가 여러개인 경우
            image_click = self.driver.find_element(By.CLASS_NAME, "carousel-inner").find_element(By.TAG_NAME, "img")
            image_click.click()
            Util.wait_time(self.logger, 3)
            image_elements = self.driver.find_element(By.CLASS_NAME, "d-none.d-md-flex.six-per-row").find_elements(By.TAG_NAME, "img")
            for image_element in image_elements:
                img_src = image_element.get_attribute("src")
                img_src = img_src.split('?')[0]
                img_srcs.append(img_src)
        else:
            if self.driver_manager.is_element_exist(By.CLASS_NAME, "carousel-inner"):
                img_src = self.driver.find_element(By.CLASS_NAME, "carousel-inner").find_element(By.TAG_NAME, "img").get_attribute("src")
                img_src = img_src.split('?')[0]
                img_srcs.append(img_src)
            else:
                self.logger.log(log_level="Event", log_msg=f"No image of product code {product_number}")

        #이미지 다운로드
        image_cnt = 1
        image_names = []
        product_code = product_code.replace("/", "-")
        if len(img_srcs) > 12:
            img_srcs = img_srcs[0:12]
        for img_src in img_srcs:
            image_name = f"{product_abbreviation}-{product_code}_{image_cnt}"
            self.driver_manager.download_image(img_src, image_name, f"./output/{output_name}/images", 0)
            image_names.append(image_name+".png")
            image_cnt += 1

        for fitment in fitments:
            info = self.product_info_factory(name=product_name, spec_name=product_spec_name, your_price=your_price, suggested_price=suggested_price,
            product_number=product_number, product_code=product_code, product_abbreviation=product_abbreviation, description=features, fitments=fitment, images=image_names)
            product_infos.append(info)
        
        return product_infos
    def save_temp_file(self):
        now = datetime.datetime.now()
        year = f"{now.year}"
        month = "%02d" % now.month
        day = f"{now.day}"
        output_name = f"{year+month+day}"
        self.save_csv_datas(f"./output", output_name)
        self.logger.log(log_level="Event", log_msg=f"Create {output_name} excel file")
    def start_crawling(self):
        
        #setting.csv 에서 세팅 값 가져오기
        try:
            self.get_settings()
        except Exception as e:
            self.logger.log(log_level="Error", log_msg=f"Error in get_settings : {e}")
        now = datetime.datetime.now()
        year = f"{now.year}"
        month = "%02d" % now.month
        day = f"{now.day}"
        output_name = f"{self.product_abbreviations[0]}-{year+month+day}"
        self.file_manager.creat_dir(f"./output/{output_name}")
        self.file_manager.creat_dir(f"./output/{output_name}/images")

        #로그인 하기
        if self.login() == False:
            return
        
        try:
            self.set_show_dealer_price()
        except Exception as e:
            self.logger.log(log_level="Error", log_msg=f"Error in set_show_dealer_price : {e}")
            return
        
        max_retry_cnt = 0
        #상품 검색
        for i in range(len(self.product_numbers)):
            try:
                urls = self.search_product(self.product_numbers[i], max_retry_cnt)
            except Exception as e:
                self.logger.log(log_level="Error", log_msg=f"Error in search_product : {e}")
                self.save_csv_datas(f"./output/{output_name}", output_name)
                return
            if max_retry_cnt > 10:
                self.save_csv_datas(f"./output/{output_name}", output_name)
                self.logger.log(log_level="Error", log_msg=f"Error in search_product 10 times, please restart the program")
            #상품을 찾은 경우에만 상세정보 크롤링 시작
            if len(urls) != 0:
                for url in urls:
                    product_infos = []
                    retry_cnt = 0
                    is_max_retried = False
                    while(not is_max_retried):
                        try:
                            product_infos = self.get_product_info(self.product_numbers[i], self.product_abbreviations[i], url, output_name)
                            is_max_retried = True
                        except Exception as e:
                            self.logger.log(log_level="Error", log_msg=f"Error in get_product_info : {e}")
                            retry_cnt += 1
                        if retry_cnt > 5:
                            is_max_retried = True

                    if len(product_infos) == 0:
                        self.product_informations.append(self.product_numbers[i])
                        self.logger.log(log_level="Error", log_msg=f"Cannot find product : {self.product_numbers[i]}")
                        self.save_csv_datas(f"./output/{output_name}", output_name)
                    else:
                        self.logger.log(log_level="Event", log_msg=f"\'{product_infos[0].spec_name}\' information crawling completed")
                        for info in product_infos:
                            self.product_informations.append(info)
            else:
                self.product_informations.append(self.product_numbers[i])
        try:
            self.save_csv_datas(f"./output/{output_name}", output_name)
        except Exception as e:
            self.logger.log(log_level="Error", log_msg=f"Error in save_csv_datas : {e}")
            return