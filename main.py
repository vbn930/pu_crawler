from Manager import DriverManager
from Utility import LoginModule
from Utility import Util
import pu_crawler
import atexit

#pyinstaller -n "PU Crawler ver1.0" --clean --onefile main.py

def main():
    logger = Util.Logger("Build")
    crawler = pu_crawler.PU_Crawler(logger)
    atexit.register(crawler.driver_manager.close_driver)
    atexit.register(crawler.save_temp_file)
    try:
        crawler.start_crawling()
        logger.log(log_level="Event", log_msg="Press enter key to exit the program")
        crawler.driver_manager.close_driver()
        exit_program = input("")
    except Exception as e:
        logger.log(log_level="Error", log_msg=e)
        crawler.driver_manager.close_driver()
main()