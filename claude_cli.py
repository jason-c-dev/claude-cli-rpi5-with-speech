import os
import logging
from colorama import init, Fore, Style
import boto3
from stt_manager import STTManager
from history_manager import HistoryManager
from claude_api_manager import ClaudeAPIManager
from log_manager import LogManager
from config_manager import ConfigManager
from audio_manager import AudioManager


class ClaudeCLI:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.log_manager = LogManager(self.config_manager)
        self.logger = self.log_manager.get_logger()
        self.history_manager = HistoryManager(self.config_manager, self.log_manager)
        self.claude_api = ClaudeAPIManager(self.config_manager, self.log_manager)
        self.show_tokens = False
        self.speech_enabled = self.config_manager.get_speech_enabled()
        self.text_output_enabled = self.config_manager.get_text_output_enabled()
        self.polly_client = boto3.client('polly',
                                         aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                                         aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                                         region_name=os.getenv("AWS_REGION"))
        self.audio_manager = AudioManager(self.config_manager, self.polly_client)
        self.stt_manager = STTManager(self.config_manager, self.log_manager)
        self.stt_enabled = self.config_manager.get_stt_enabled()
        self.logger.info("ClaudeCLI initialized successfully")

    async def send_message(self, message):
        response = await self.claude_api.send_message(
            message, 
            self.history_manager.get_history(), 
            self.speech_enabled, 
            self.text_output_enabled, 
            self.show_tokens, 
            self.audio_manager
        )
        self.history_manager.add_message("user", message)
        self.history_manager.add_message("assistant", response)
        self.history_manager.save_history()  # Save history once after both messages are added

    async def display_history(self):
        self.logger.info("Displaying conversation history")
        for entry in self.history_manager.history:
            role = entry["role"].capitalize()
            content = entry["content"]
            color = Fore.YELLOW if role == "User" else Fore.GREEN
            print(f"{color}{role}: {content}{Style.RESET_ALL}")
            if self.show_tokens:
                tokens = await self.claude_api.count_tokens(content)
                print(f"{Fore.CYAN}Tokens: {tokens}{Style.RESET_ALL}")
            print()

    def display_system_prompt(self):
        self.logger.info("Displaying system prompt")
        print(f"{Fore.CYAN}Current system prompt:")
        print(f"{self.claude_api.system_prompt}{Style.RESET_ALL}")

    def display_model(self):
        self.logger.info("Displaying model information")
        print(f"{Fore.CYAN}Current model: {self.claude_api.model}")
        print(f"Max tokens: {self.claude_api.max_tokens}")
        print(f"Log level: {self.logger.level}{Style.RESET_ALL}")

    def toggle_tokens(self):
        self.show_tokens = not self.show_tokens
        status = "on" if self.show_tokens else "off"
        logging.info(f"Token display toggled {status}")
        print(f"{Fore.MAGENTA}Token display is now {status}.{Style.RESET_ALL}")

    def toggle_speech(self):
        self.speech_enabled = not self.speech_enabled
        status = "on" if self.speech_enabled else "off"
        logging.info(f"Speech output toggled {status}")
        print(f"{Fore.MAGENTA}Speech output is now {status}.{Style.RESET_ALL}")

    def toggle_text_output(self):
        self.text_output_enabled = not self.text_output_enabled
        status = "on" if self.text_output_enabled else "off"
        logging.info(f"Text output toggled {status}")
        print(f"{Fore.MAGENTA}Text output is now {status}.{Style.RESET_ALL}")

    def clear_history(self):
        self.history_manager.clear_history()
        print(f"{Fore.MAGENTA}Conversation history cleared and backed up.{Style.RESET_ALL}")

    def display_help(self):
        logging.info("Displaying help information")
        print(f"{Fore.CYAN}Available commands:")
        print("  exit    - Quit the application")
        print("  system  - Display the current system prompt")
        print("  history - Show the conversation history")
        print("  model   - Display the current Claude model being used")
        print("  clear   - Clear the conversation history (creates a backup)")
        print("  tokens  - Toggle the display of token counts")
        print("  speech  - Toggle speech output")
        print("  text    - Toggle text output")
        print("  stt     - Toggle Speech-to-Text input")
        print(f"  help    - Display this help message{Style.RESET_ALL}")

    def toggle_stt(self):
        self.stt_enabled = not self.stt_enabled
        status = "on" if self.stt_enabled else "off"
        self.logger.info(f"Speech-to-Text toggled {status}")
        print(f"{Fore.MAGENTA}Speech-to-Text is now {status}.{Style.RESET_ALL}")
    
    async def run(self):
        try:
            self.logger.info("Starting Claude CLI")
            print(f"{Fore.MAGENTA}Welcome to the Claude CLI. Type 'help' for available commands or 'exit' to quit.{Style.RESET_ALL}")
            while True:
                if self.stt_enabled:
                    try:
                        user_input = await self.stt_manager.listen_for_speech()
                        if user_input is None:
                            continue  # Skip this iteration and prompt for input again
                        if user_input == "GOODBYE_DETECTED":
                            self.logger.info("Exiting Claude CLI due to 'goodbye' detection")
                            break
                        print(f"{Fore.YELLOW}You: {user_input}{Style.RESET_ALL}")
                    except Exception as e:
                        self.logger.error(f"Error in speech recognition: {str(e)}")
                        print(f"{Fore.RED}Speech recognition failed. Please type your input.{Style.RESET_ALL}")
                        user_input = input(f"{Fore.YELLOW}You: {Style.RESET_ALL}").strip()
                else:
                    user_input = input(f"{Fore.YELLOW}You: {Style.RESET_ALL}").strip()

                if not user_input:
                    continue  # Skip empty input

                self.logger.debug(f"User input: {user_input}")

                if user_input.lower() == 'exit':
                    self.logger.info("Exiting Claude CLI")
                    break
                elif user_input.lower() == 'system':
                    self.display_system_prompt()
                elif user_input.lower() == 'history':
                    await self.display_history()
                elif user_input.lower() == 'model':
                    self.display_model()
                elif user_input.lower() == 'clear':
                    self.clear_history()
                elif user_input.lower() == 'tokens':
                    self.toggle_tokens()
                elif user_input.lower() == 'speech':
                    self.toggle_speech()
                elif user_input.lower() == 'text':
                    self.toggle_text_output()
                elif user_input.lower() == 'stt':
                    self.toggle_stt()
                elif user_input.lower() == 'help':
                    self.display_help()
                else:
                    await self.send_message(user_input)
        finally:
            self.shutdown()

    def shutdown(self):
        self.logger.info("Shutting down Claude CLI")
        if hasattr(self.stt_manager, 'stop_audio'):
            self.stt_manager.stop_audio.set()
        self.audio_manager.shutdown()
        self.logger.info("Claude CLI shutdown complete")