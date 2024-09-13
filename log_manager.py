import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from dotenv import load_dotenv
from colorama import init, Fore, Style

class LogManager:
    def __init__(self, config_manager, log_dir="logs"):
        self.config_manager = config_manager
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.setup_logging()

    def setup_logging(self):
        log_level_str = self.config_manager.get_log_level()
        log_file = os.path.join(self.log_dir, "claude_cli.log")

        try:
            log_level = getattr(logging, log_level_str.upper())
            
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)
            
            logger = logging.getLogger()
            logger.setLevel(log_level)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=1024 * 1024,  # 1 MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

            logging.info(f"Logging initialized. Level: {log_level_str}, File: {log_file}")

        except Exception as e:
            print(f"Error setting up logging: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Attempted log file path: {os.path.abspath(log_file)}")

    def get_logger(self):
        return logging.getLogger()