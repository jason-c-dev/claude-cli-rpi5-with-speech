import os
import json
from datetime import datetime
from dotenv import load_dotenv
from colorama import init, Fore, Style


class HistoryManager:
    def __init__(self, config_manager, log_manager):
        self.config_manager = config_manager
        self.logger = log_manager.get_logger()
        self.log_dir = log_manager.log_dir
        self.history = self.load_history()

    def load_history(self):
        history_file = os.path.join(self.log_dir, "history.json")
        try:
            with open(history_file, "r", encoding='utf-8') as f:
                history = json.load(f)
            self.logger.info("Conversation history loaded successfully")
            return history
        except FileNotFoundError:
            self.logger.warning("history.json not found. Starting with empty history.")
            return []
        except json.JSONDecodeError:
            self.logger.error("Error decoding history.json. Starting with empty history.")
            return []

    def save_history(self):
        history_file = os.path.join(self.log_dir, "history.json")
        with open(history_file, "w", encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
        self.logger.info("Conversation history saved")

    def backup_history(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"history_backup_{timestamp}.json"
        backup_file = os.path.join(self.log_dir, backup_filename)
        with open(backup_file, "w", encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Conversation history backed up to {backup_filename}")

    def clear_history(self):
        self.logger.info("Clearing conversation history")
        self.backup_history()
        self.history = []
        self.save_history()


    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})
        # Removed self.save_history() from here

    def get_recent_history(self, num_messages=10):
        return self.history[-num_messages:] if len(self.history) > num_messages else self.history