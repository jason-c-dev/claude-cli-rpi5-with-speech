import json
import logging
from dotenv import load_dotenv
from colorama import init, Fore, Style

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)
            logging.info("Configuration loaded successfully")
            return config
        except FileNotFoundError:
            logging.warning(f"{self.config_file} not found. Using default configuration.")
            return {}
        except json.JSONDecodeError:
            logging.error(f"Error decoding {self.config_file}. Using default configuration.")
            return {}

    def get(self, key, default=None):
        return self.config.get(key, default)

    def get_model(self):
        return self.get("model", "claude-3-sonnet-20240229")

    def get_max_tokens(self):
        return self.get("max_tokens", 4096)

    def get_speech_enabled(self):
        return self.get("speech_enabled", True)

    def get_text_output_enabled(self):
        return self.get("text_output_enabled", True)

    def get_stt_enabled(self):
        return self.get("stt_enabled", False)

    def get_deepgram_model(self):
        return self.get("deepgram_model", "general")

    def get_log_level(self):
        return self.get("log_level", "INFO")

    def get_system_prompt_file(self):
        return self.get("system_prompt_file", "system_prompt.txt")

    def get_aws_polly_voice(self):
        return self.get("aws_polly_voice", "Ruth")

    def get_aws_polly_engine(self):
        return self.get("aws_polly_engine", "neural")