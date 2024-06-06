import time
from datetime import datetime
from googletrans import Translator

def translator(src, dst, trans_str):
    translator = Translator(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
    result_str = translator.translate(text=trans_str, src=src, dest=dst).text
    time.sleep(2)
    return result_str

def wait_time(logger, wait_time):
    logger.log(log_level="Debug", log_msg=f"Wait {wait_time} secs")
    time.sleep(wait_time)

class Logger:
    def __init__(self, log_level):
        self.log_level = log_level
        self.log_stack = list()

    def save_logs(self):
        file_path = "log.txt"
        with open(file_path, "w") as file:
            for log in self.log_stack:
                file.write(log + "\n")
        
    def clear_log_stack(self):
        self.log_stack.clear()
    
    #로그 타입 Debug, Info, Event, Error
    def log(self, log_level = "Debug", log_msg = "Null"):
        now = datetime.now()
        msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}][{log_level}] {log_msg}"
        self.log_stack.append(msg)
        if self.log_level == "Dev":
            print(msg)
        elif self.log_level == "Build":
            if log_level == "Event" or log_level == "Error":
                print(msg)
        if log_level == "Error":
            self.save_logs()
            