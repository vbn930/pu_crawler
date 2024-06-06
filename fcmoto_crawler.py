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
    product_code: str
    name: str
    category: str
    description: str
    trans_description: str
    original_price: str
    dealer_price: str
    option_names: list
    option_values: list
    images: list

class FCMOTO_Crawler:

    def __init__(self, logger):
        self.product_code_count = 1
        self.product_informations = []
        self.data = dict()
        self.data_init()
        self.file_manager = FileManager.FileManager()
        self.logger = logger
        self.driver_manager = DriverManager.WebDriverManager(self.logger, False)
        self.is_setting_complete = False
        self.is_exit = False
        self.file_manager.creat_dir("./temp")
        self.file_manager.creat_dir("./output")

    def data_init(self):
        self.data.clear()
        self.data["상품코드"] = list()
        self.data["상품명"] = list()
        self.data["카테고리"] = list()
        self.data["설명"] = list()
        self.data["설명 번역"] = list()
        self.data["정상가"] = list()
        self.data["딜러가"] = list()
        self.data["대표 이미지"] = list()
        self.data["상세 이미지"] = list()
        self.data["옵션명"] = list()
        self.data["옵션 내용"] = list()

    def print_product_info(self, product_info: ProductInfo):
        print(f"===============================================================================================================")
        print(f"Product code : {product_info.product_code}")
        print(f"Product name : {product_info.name}")
        print(f"Product category : {product_info.category}")
        print(f"Product description : {product_info.description}")
        print(f"Product price : original \'{product_info.original_price}\', dealer \'{product_info.dealer_price}\'")
        print(f"Product options : {product_info.option_names}, {product_info.option_values}")
        print(f"Product image names : {product_info.images}")
        print(f"===============================================================================================================")
    
    def print_product_info_all(self):
        for info in self.product_informations:
            self.print_product_info(info)

    #중복 상품 등록 방지
    def check_list_element_is_exist(self, target_list: list, element):
        is_same = False
        for item in target_list:
            if item == element:
                is_same = True
                break
        return is_same
    
    def save_csv_datas(self, dir_path, file_name):
        for product_info in self.product_informations:
            self.product_info_formating(product_info)
        data_frame = pd.DataFrame(self.data)
        data_frame.to_csv(f"{dir_path}/{file_name}.csv", index=False, encoding="utf-8-sig")
        
        #data_frame.to_excel(f"{dir_path}/{file_name}.xls", index=False)
        return

    #pandas csv 데이터 타입으로 포멧팅 후 저장
    def product_info_formating(self, product_info: ProductInfo):
        self.data["상품코드"].append(product_info.product_code)
        self.data["상품명"].append(product_info.name)
        self.data["카테고리"].append(product_info.category)
        self.data["설명"].append(product_info.description)
        self.data["설명 번역"].append(product_info.trans_description)
        self.data["정상가"].append(product_info.original_price)
        self.data["딜러가"].append(product_info.dealer_price)
        self.data["대표 이미지"].append(product_info.images[0])

        product_img = ""
        for img in product_info.images:
            product_img += img
            if img != product_info.images[-1]:
                product_img += "|"
        self.data["상세 이미지"].append(product_img)

        option_name = ""
        for name in product_info.option_names:
            option_name += name
            if name != product_info.option_names[-1]:
                option_name += "|"
        self.data["옵션명"].append(option_name)

        option_value = ""
        for option_list in product_info.option_values:
            options = ""
            for option in option_list:
                options += option
                if option != option_list[-1]:
                    options += ";"
            option_value += options
            if option_list != product_info.option_values[-1]:
                option_value += "|" 
        self.data["옵션 내용"].append(option_value)
        return

    def product_info_factory(self, brand_name: str, brand_code: str, product_code: str, product_name: str, product_category: list, product_description: str, 
        product_original_price: str, product_dealer_price: str, product_options: dict, product_images: list):

        #temp 에 저장된 사진들 분류
        #file path
        '''
        {크롤링년,월_브랜드 이름}
            ->{크롤링년,월_브랜드 이름}.xls
            ->{크롤링년,월_브랜드 이름_images}
                ->{상품코드_일련번호}
                    ->이미지들
        '''
        for img in product_images:
            self.file_manager.move_file(file_name=img, src="./temp", dst=f"./output/{brand_code}/{brand_code}_images")
        

        #카테고리 한문장으로 포멧팅
        category = ""
        temp_list = product_category.copy()
        temp_list.reverse()
        product_category_list = temp_list
        product_category_list.pop()
        for name in product_category_list:
            category += name
            if name != product_category_list[-1]:
                category += "/"
        
        #여러 버튼 옵션들 리스트로 정리 -> 리스트 내부에 각 옵션 리스트(첫번째 값이 옵션 명, 그 이후는 옵션 값)
        option_values = []
        option_name = []
        for key, value in product_options.items():
            option_name.append(key)
            option_values.append(value)
        
        #디스크립션 번역
        product_description = product_description.replace("\n","|")
        trans_description = Util.translator("en", "ko", product_description)

        info = ProductInfo(product_code=product_code, name=product_name, category=category, description=product_description, trans_description=trans_description, 
            original_price=product_original_price, dealer_price=product_dealer_price, option_names=option_name, option_values=option_values, images=product_images)
        #self.print_product_info(info)
        
        return info

    def start_crawling(self):
        #cvs 파일에서 계정 정보, 브랜드, 브랜드 코드 가져오기
        data = pd.read_csv("./setting.csv").fillna(0)
        brand = data["brand"].to_list()
        brand.append(0)
        brand = brand[0:brand.index(0)]
        brand_code = data["brand_code"].to_list()
        brand_code.append(0)
        brand_code = brand_code[0:brand_code.index(0)]
        account = data["account"].to_list()
        account.append(0)
        account = account[0:account.index(0)]

        id = account[0]
        pw = account[1]

        self.logger.log(log_level="Event", log_msg="FCMOTO crawler")
        self.logger.log(log_level="Event", log_msg=f"ID : {id}, PW : {pw}")
        #로그인 -> search_brand(페이지 수 받아오기) -> product_search_page(각 페이지 상품 가져오기)
        driver_manager = self.driver_manager

        max_try_cnt = 5
        is_login_succes = False
        self.is_setting_complete = False
        for i in range(max_try_cnt):
            self.logger.log("Debug", f"is_login_succes : {is_login_succes}, is_setting_complete : {self.is_setting_complete}")
            if is_login_succes and self.is_setting_complete:
                break
            try:
                if is_login_succes == False:
                    is_login_succes = LoginModule.fcmoto_login_module(driver_manager, self.logger, id, pw)
                    if is_login_succes == False:
                        driver_manager.logger.log(log_level="Error", log_msg="Login failed")
                if self.is_setting_complete == False:
                    self.is_setting_complete =  self.set_currency_and_lang()
            except Exception as e:
                self.logger.log(log_level="Error", log_msg=e)
        if is_login_succes == False or self.is_setting_complete == False:
            if is_login_succes == False:
                driver_manager.logger.log(log_level="Error", log_msg="Login failed, check again your account information in setting.csv or launch the program again")
                return
            if self.is_setting_complete == False:
                self.logger.log(log_level="Error", log_msg="Currency and Language setting failed. Please restart the program")
                return
        driver_manager.is_headless = True
        now = datetime.datetime.now()
        year = f"{now.year}"[-2:]
        month = "%02d" % now.month
        for i in range(len(brand)):
            code = brand_code[i] + year + month
            self.search_brand(driver_manager, brand[i], code)
            self.save_csv_datas(f"./output/{code}", f"{year + month}_{brand[i]}")

            #csv 데이터 생성 후 초기화
            self.data_init()
            self.product_informations.clear()
            self.product_code_count = 1
    
    #가격 정보 변경
    def set_currency_and_lang(self):
        is_changed = False
        driver = self.driver_manager.driver
        url = "https://www.fc-moto.de/epages/fcm.sf/en_KR/?ViewAction=View&ObjectID=2587640"
        self.driver_manager.get_page(url)
        hidden_tab = driver.find_element(By.CLASS_NAME, "ICLocaleCountry")
        ActionChains(driver).move_to_element(hidden_tab).perform()
        select_element = driver.find_element(By.NAME, 'Currency')
        select = Select(select_element)
        select.select_by_value("EUR")
        select_element = driver.find_element(By.NAME, 'Language')
        select = Select(select_element)
        select.select_by_value("2")
        button = driver.find_element(By.CLASS_NAME, "CountrySelectorButton.ep-js")
        ActionChains(driver).move_to_element(button).click().perform()
        driver.implicitly_wait(10)
        result = driver.find_element(By.CLASS_NAME, "ICLocaleCountry").text
        if result.find("€") != -1:
            is_changed = True
        return is_changed

    def search_brand(self, driver_manager, brand_name, brand_code):
        #브랜드 코드로 폴더 만들어서 파일들 저장
        self.file_manager.creat_dir(f"./output/{brand_code}")
        self.file_manager.creat_dir(f"./output/{brand_code}/{brand_code}_images")
        
        #브랜드 검색해서 페이지 수 받아오고 product_search_page 함수 돌리는 함수
        driver = driver_manager.get_driver()
        product_search_url = f"https://www.fc-moto.de/epages/fcm.sf/ko_KR/?ViewAction=FacetedSearchProducts&ObjectPath=/Shops/10207048&Page=1&OrderBy=Newness&OrderDesc=1&SearchString={brand_name}&PageSize=72"
        
        #마지막 상품 페이지 찾기
        driver_manager.get_page(product_search_url)
        page_nums = []
        last_page = 1
        if driver_manager.is_element_exist(By.CLASS_NAME, "PagerSizeContainer"):
            page_nums = driver.find_element(By.CLASS_NAME, "PagerSizeContainer").find_elements(By.TAG_NAME, "a")
            last_page = int(page_nums[-2].text)
        
        #상품 마지막 페이지 까지 데이터 추출
        product_check_info = [] #중복 상품 추출 방지를 위한 상품 이름 리스트
        self.logger.log(log_level="Event", log_msg=f"Brand name \'{brand_name}\'(brand code \'{brand_code}\') crawling start! Total pages are {last_page} pages")
        for page in range(last_page):
            self.logger.log(log_level="Event", log_msg=f"Current brand : {brand_name}, Current page : {page + 1}")
            self.product_search_page(driver_manager, brand_name, brand_code, page + 1, product_check_info)
            self.logger.clear_log_stack()

    def product_search_page(self, driver_manager, brand_name, brand_code, page, product_check_info):
        driver = driver_manager.get_driver()
        product_search_url = f"https://www.fc-moto.de/epages/fcm.sf/ko_KR/?ViewAction=FacetedSearchProducts&ObjectPath=/Shops/10207048&Page={page}&OrderBy=Newness&OrderDesc=1&SearchString={brand_name}&PageSize=72"
        product_name_css_selector = "#div > div.ListItemProductInfoContainer > div.ListItemProductTopFloatArea > h3 > a"
        driver_manager.get_page(product_search_url)
        product_areas = driver.find_elements(By.CLASS_NAME, "ListItemProductContainer.ProductDetails")

        product_hrefs = []

        for product_area in product_areas:
            product_info = product_area.find_element(By.CLASS_NAME, "ListItemProductInfoContainer").find_element(By.CLASS_NAME, "Headline")
            product_info_name = product_info.find_element(By.CSS_SELECTOR, "div.ListItemProductTopFloatArea > h3 > a").get_attribute("title")
            product_info_price = product_area.find_element(By.CLASS_NAME, "ListItemProductInfoContainer").find_elements(By.CLASS_NAME, "PriceArea")[1].text
            if self.check_list_element_is_exist(product_check_info, [product_info_name, product_info_price]) == False:
                product_check_info.append([product_info_name, product_info_price])
                href = product_info.find_element(By.CSS_SELECTOR, "div.ListItemProductTopFloatArea > h3 > a").get_attribute("href")
                product_hrefs.append(href)
        
        max_retry_cnt = 5
        for product_href in product_hrefs:
            #상품 크롤링 실패시 다시 크롤링
            is_finish_search = False
            current_info_cnt = self.product_code_count
            for i in range(max_retry_cnt):
                try:
                    if is_finish_search == False:
                        self.product_info_page(driver_manager, brand_name, brand_code, product_href)
                        is_finish_search = True
                except:
                    self.logger.log(log_level="Error", log_msg=f"Failed to get information of \'{product_href}\' trying to get information again!")
                    saved_product_infos = self.product_code_count - current_info_cnt
                    for i in range(saved_product_infos):
                        self.product_informations.pop()
                    self.product_code_count -= saved_product_infos
            self.logger.save_logs()
        
    def product_info_page(self, driver_manager, brand_name, brand_code, prodcut_url):
        driver = driver_manager.get_driver()
        driver_manager.get_page(prodcut_url)
        prodcut_name = driver.find_element(By.CSS_SELECTOR, "div.ICProductContentWrapper.ProductDetails > div.ICRightHalf > div.ICProductVariationArea > h1").text
        self.logger.log(log_level="Debug", log_msg=f"product name : {prodcut_name}")

        #저장된 상품 개수
        saved_product_infos = 0

        #상세 이미지 저장 최대 개수
        max_img_cnt = 12

        product_price_original = ""
        product_price_dealer = ""
        product_price_dict = dict()
        #할인 상품이라면 가격 정보가 두개 -> 할인 상품이 아니라면 PriceAndTaxInfo의 가격만 존재 
        try:
            product_price_original = driver.find_element(By.CLASS_NAME, "PriceArea.InsteadOf").find_element(By.CLASS_NAME, "LineThrough").text[:-2]
            product_price_dealer = driver.find_element(By.CLASS_NAME, "PriceAndTaxInfo").find_element(By.TAG_NAME, "span").text[:-2]
            if product_price_original == "":
                product_price_original = product_price_dealer
        except NoSuchElementException:
            product_price_original = driver.find_element(By.CLASS_NAME, "PriceAndTaxInfo").find_element(By.TAG_NAME, "span").text[:-2]
            product_price_dealer = product_price_original
        self.logger.log(log_level="Debug", log_msg=f"product price : {product_price_original}, {product_price_dealer}")

        img_option_names = []
        button_option_names = []
        img_option_values = []
        button_option_values = []

        image_option_dict = dict() #img_option_name(string): img_option_value(list)
        button_option_dict = dict()
        button_option_dicts = dict()

        #상품 카테고리 파싱
        product_category = []
        category_elements = driver.find_elements(By.CLASS_NAME, "BreadcrumbItem")
        for category_element in category_elements:
            category = category_element.find_element(By.TAG_NAME, "span").text
            product_category.append(category)

        #이미지 파일 링크들
        product_image_dict = dict() #key = 옵션 이름, value = 이미지 링크들 or 이미지 이름

        #이미지가 없는 상품 옵션 제목 파싱
        if driver_manager.is_element_exist(By.CLASS_NAME, "Headline.button") == True:
            option_name_elements = driver.find_elements(By.CLASS_NAME, "Headline.button")
            for option_name_element in option_name_elements:
                option_name = option_name_element.find_element(By.TAG_NAME, "span").text[:-1]
                button_option_names.append(option_name)

        #이미지가 존재하는 상품 옵션 제목 파싱
        if driver_manager.is_element_exist(By.CLASS_NAME, "Headline.image") == True:
            option_name_elements = driver.find_elements(By.CLASS_NAME, "Headline.image")
            for option_name_element in option_name_elements:
                option_name = option_name_element.find_element(By.TAG_NAME, "span").text[:-1]
                img_option_names.append(option_name)

        #상품 세부 옵션들 파싱
        if driver_manager.is_element_exist(By.CLASS_NAME, "ICAttributBar") == True:
            ICAttributBars = driver.find_elements(By.CLASS_NAME, "ICAttributBar")
            for ICAttributBar in ICAttributBars:
                if driver_manager.is_element_exist(By.TAG_NAME, "img") == True:
                    img_option_vals = []
                    for option in ICAttributBar.find_elements(By.TAG_NAME, "img"):
                        option_title = option.get_attribute("title")
                        img_option_vals.append(option_title)
                        #이미지가 존재하는 옵션 클릭해서 상품 이미지 파싱
                        option.click()
                        Util.wait_time(self.logger, 3)
                        driver.implicitly_wait(10)
                        #상품 옵션별로 가격 다시 크롤링
                        #할인 상품이라면 가격 정보가 두개 -> 할인 상품이 아니라면 PriceAndTaxInfo의 가격만 존재 
                        price = []
                        try:
                            original = driver.find_element(By.CLASS_NAME, "PriceArea.InsteadOf").find_element(By.CLASS_NAME, "LineThrough").text[:-2]
                            dealer = driver.find_element(By.CLASS_NAME, "PriceAndTaxInfo").find_element(By.TAG_NAME, "span").text[:-2]

                            if original == "":
                                original = dealer

                            #일반 가격
                            price.append(original)
                            #딜러 가격
                            price.append(dealer)
                        except NoSuchElementException:
                            temp_price = driver.find_element(By.CLASS_NAME, "PriceAndTaxInfo").find_element(By.TAG_NAME, "span").text[:-2]
                            price.append(temp_price)
                            price.append(temp_price)
                        product_price_dict[option_title] = price

                        #ICAttributBars 다시 로드 (클릭 후 페이지 코드가 변경되므로 element 새로 로드)
                        #button 옵션이 존재할 경우에만 크롤링
                        if driver_manager.is_element_exist(By.CLASS_NAME, "ICAttributBar") and driver_manager.is_element_exist(By.TAG_NAME, "button"):
                            reloaded_ICAttributBars = driver.find_elements(By.CLASS_NAME, "ICAttributBar")
                            for reloaded_ICAttributBar in reloaded_ICAttributBars:
                                #여기에서 상품 정보 다시 크롤링
                                if driver_manager.is_element_exist(By.TAG_NAME, "button") and len(reloaded_ICAttributBar.find_elements(By.TAG_NAME, "button")) != 0:
                                    button_option_vals = []
                                    for item_option in reloaded_ICAttributBar.find_elements(By.TAG_NAME, "button"):
                                        button_option_vals.append(item_option.text)
                                    if len(button_option_vals) != 0:
                                        button_option_values.append(button_option_vals)
                                
                                    if len(button_option_names) != 0:
                                        for i in range(len(button_option_names)):
                                            button_option_dict[button_option_names[i]] = button_option_values[i]
                                        button_option_dicts[option_title] = button_option_dict.copy()
                                        button_option_dict = dict()
                                    button_option_values = []
                        
                        image_elements = []
                        is_single_img = False
                        if driver_manager.is_element_exist(By.ID, "ProductThumbBar") == True: #여러개의 상품 이미지가 존재하는 경우
                            image_elements = driver.find_element(By.ID, "ProductThumbBar").find_elements(By.TAG_NAME, "img")
                        else: #이미지가 대표 이미지 하나만 있는 경우
                            image_elements = [driver.find_element(By.ID, "ICImageMediumLarge")]
                            is_single_img = True
                        image_urls = []
                        img_cnt = 1
                        for image_element in image_elements:
                            img_url = image_element.get_attribute("src")
                            if is_single_img: #대표 이미지 하나만 있는 경우에는 이미지 링크의 마지막 _S 키워드가 없어서 원본을 다운로드 하면됨
                                img_url = img_url[:-4] + img_url[-4:]
                            else:
                                img_url = img_url[:-6] + img_url[-4:]
                            
                            image_urls.append(img_url)
                            img_cnt += 1
                        product_image_dict[option_title] = image_urls
                    if len(img_option_vals) != 0:
                        img_option_values.append(img_option_vals)
                
                if driver_manager.is_element_exist(By.TAG_NAME, "button") == True:
                    button_option_vals = []
                    for option in ICAttributBar.find_elements(By.TAG_NAME, "button"):
                        button_option_vals.append(option.text)
                    if len(button_option_vals) != 0:
                        button_option_values.append(button_option_vals)

        #이름과 밸류로 이분화된 옵션 데이터들을 딕셔너리 자료형으로 정리
        if len(img_option_names) != 0:
            for i in range(len(img_option_names)):
                image_option_dict[img_option_names[i]] = img_option_values[i]
        
        if len(button_option_names) != 0:
            for i in range(len(button_option_names)):
                button_option_dict[button_option_names[i]] = button_option_values[i]

        #상품 상세 설명 라인 받아오기 (타입은 문자열)
        description_line = driver.find_element(By.CLASS_NAME, "description").text

        #만약 이미지 옵션이 없는 상품이라면 상품 이미지를 다운로드 하지 않은 상태라서 따로 여기서 다운로드 해주어야함
        if len(img_option_names) == 0:
            is_single_img = False
            image_elements = []
            if driver_manager.is_element_exist(By.ID, "ProductThumbBar") == True: #여러개의 상품 이미지가 존재하는 경우
                image_elements = driver.find_element(By.ID, "ProductThumbBar").find_elements(By.TAG_NAME, "img")
            else: #이미지가 대표 이미지 하나만 있는 경우
                image_elements = [driver.find_element(By.ID, "ICImageMediumLarge")]
                is_single_img = True
            image_urls = []
            image_names = []
            img_cnt = 1

            #이미지 파일 이름은 상품 코드와 이미지 번호 조합
            product_num_format = "%04d" % self.product_code_count
            product_code = f"{brand_code}-{product_num_format}"

            for image_element in image_elements:
                img_url = image_element.get_attribute("src")
                if is_single_img: #대표 이미지 하나만 있는 경우에는 이미지 링크의 마지막 _S 키워드가 없어서 원본을 다운로드 하면됨
                    img_url = img_url[:-4] + img_url[-4:]
                else:
                    img_url = img_url[:-6] + img_url[-4:]
                if img_cnt < max_img_cnt + 1:
                    image_urls.append(img_url)
                    image_name = f"{product_code}_{img_cnt}"
                    image_names.append(image_name+".jpg")
                    driver_manager.download_image(img_url, image_name, "./temp", 0)
                    img_cnt += 1
            self.product_informations.append(self.product_info_factory(
                    brand_name=brand_name, brand_code=brand_code,product_code=product_code, product_name=f"{prodcut_name}", product_category=product_category
                    , product_description=description_line, product_original_price=product_price_original, product_dealer_price=product_price_dealer, product_options=button_option_dict
                    , product_images=image_names))
            self.product_code_count += 1 #객체를 클래스 리스트에 추가 후 카운트 + 1
        
        else: #이미지 옵션이 존재하는 경우 반복문으로 옵션 별로 상품 모두 리스트에 저장
            for img_option_name in img_option_names: #img_option_name은 옵션의 이름 (ex-Color)
                for image_option in image_option_dict[img_option_name]: #image_options는 옵션 내부의 옵션 값들 (ex-black, white, red)
                    image_names = []
                    img_cnt = 1
                    
                    #이미지 파일 이름은 상품 코드와 이미지 번호 조합
                    product_num_format = "%04d" % self.product_code_count
                    product_code = f"{brand_code}-{product_num_format}"

                    for imag_url in product_image_dict[image_option]: #옵션 내부의 값을 product_image_dict 키로 넣으면 이미지의 링크들이 담긴 리스트 반환
                        image_name = f"{product_code}_{img_cnt}"
                        if img_cnt < max_img_cnt + 1:
                            driver_manager.download_image(imag_url, image_name, "./temp", 0) #다운로드된 이미지는 temp 폴더에 저장
                            image_names.append(image_name+".jpg")
                        img_cnt += 1
                    option_dict = dict()
                    if len(button_option_dicts) == 0:
                        option_dict = button_option_dict
                    else:
                        option_dict = button_option_dicts[image_option]
                    # * 이미지 옵션이 존재 하는 경우에만 * 여기서 이미지 옵션별로 상품 정보 객체 생성 
                    self.product_informations.append(self.product_info_factory(
                        brand_name=brand_name, brand_code=brand_code,product_code=product_code, product_name=f"{prodcut_name}({image_option})", product_category=product_category
                        , product_description=description_line, product_original_price=product_price_dict[image_option][0], product_dealer_price=product_price_dict[image_option][1], product_options=option_dict
                        , product_images=image_names))
                    self.product_code_count += 1 #객체를 클래스 리스트에 추가 후 카운트 + 1

        self.logger.log(log_level="Event", log_msg=f"\'{prodcut_name}\' information crawling completed")
