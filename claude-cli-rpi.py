import os
import json
import asyncio
import threading
from queue import Queue
import re
import logging
from datetime import datetime
import tempfile
import uuid

from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from colorama import init, Fore, Style
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import pygame

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()

# Initialize pygame mixer
pygame.mixer.init()

class ClaudeCLI:
    def __init__(self):
        self.config = self.load_config()
        self.setup_logging()
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.history = self.load_history()
        self.system_prompt = self.config.get("system_prompt", "You are a helpful AI assistant.")
        self.model = self.config.get("model", "claude-3-sonnet-20240229")
        self.max_tokens = self.config.get("max_tokens", 4096)
        self.show_tokens = False
        self.speech_enabled = self.config.get("speech_enabled", True)
        self.text_output_enabled = self.config.get("text_output_enabled", True)
        self.aws_polly_voice = self.config.get("aws_polly_voice", "Ruth")
        self.aws_polly_engine = self.config.get("aws_polly_engine", "neural")
        self.polly_client = boto3.client('polly', 
                                         aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                                         aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                                         region_name=os.getenv("AWS_REGION"))
        self.audio_queue = Queue()
        self.audio_thread = threading.Thread(target=self.audio_player_thread, daemon=True)
        self.audio_thread.start()

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def setup_logging(self):
        log_level = self.config.get("log_level", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.info(f"Logging level set to {log_level}")

    def load_history(self):
        try:
            with open("history.json", "r", encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            logging.error("Error decoding history.json. Starting with empty history.")
            return []

    def save_history(self):
        with open("history.json", "w", encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
        logging.info("Conversation history saved.")

    def backup_history(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"history_backup_{timestamp}.json"
        with open(backup_filename, "w", encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
        logging.info(f"Conversation history backed up to {backup_filename}")

    def format_messages(self, message):
        messages = self.history + [{"role": "user", "content": message}]
        return messages

    async def count_tokens(self, text):
        return await self.client.count_tokens(text)

    def audio_player_thread(self):
        while True:
            audio_file = self.audio_queue.get()
            if audio_file is None:  # None is our signal to stop
                break
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            os.remove(audio_file)  # Clean up the file after playing
            self.audio_queue.task_done()

    async def text_to_speech(self, text, sequence_number):
        try:
            response = self.polly_client.synthesize_speech(
                Engine=self.aws_polly_engine,
                LanguageCode='en-US',
                Text=text,
                TextType='text',
                OutputFormat='mp3',
                VoiceId=self.aws_polly_voice
            )

            if "AudioStream" in response:
                file_name = f"speech_{sequence_number}_{uuid.uuid4()}.mp3"
                file_path = os.path.join(tempfile.gettempdir(), file_name)
                
                with open(file_path, 'wb') as file:
                    file.write(response['AudioStream'].read())
                
                return file_path
            else:
                logging.error("No AudioStream found in the response")
                return None

        except (BotoCoreError, ClientError) as error:
            logging.error(f"AWS Polly error: {error}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in text_to_speech: {str(e)}")
            return None

    async def send_message(self, message):
        max_retries = 5
        base_delay = 1
        sequence_number = 0

        async def process_sentence(sentence):
            nonlocal sequence_number
            if self.speech_enabled and sentence.strip():
                file_path = await self.text_to_speech(sentence.strip(), sequence_number)
                if file_path:
                    self.audio_queue.put(file_path)
                    sequence_number += 1

        for attempt in range(max_retries):
            try:
                messages = self.format_messages(message)
                input_tokens = await self.count_tokens(json.dumps(messages) + self.system_prompt)
                
                if self.show_tokens:
                    print(f"{Fore.CYAN}Input tokens: {input_tokens}{Style.RESET_ALL}")

                stream = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=messages,
                    system=self.system_prompt,
                    stream=True
                )

                full_response = ""
                sentence_buffer = ""
                if self.text_output_enabled:
                    print(f"{Fore.GREEN}Claude: ", end='', flush=True)

                async for chunk in stream:
                    if chunk.type == "content_block_delta":
                        if chunk.delta.text:
                            if self.text_output_enabled:
                                print(f"{Fore.GREEN}{chunk.delta.text}", end='', flush=True)
                            full_response += chunk.delta.text
                            sentence_buffer += chunk.delta.text
                            
                            while True:
                                sentence_end = sentence_buffer.find('.')
                                if sentence_end == -1:
                                    sentence_end = sentence_buffer.find('!')
                                if sentence_end == -1:
                                    sentence_end = sentence_buffer.find('?')
                                if sentence_end == -1:
                                    break
                                
                                sentence = sentence_buffer[:sentence_end+1]
                                await process_sentence(sentence)
                                sentence_buffer = sentence_buffer[sentence_end+1:].lstrip()

                    elif chunk.type == "message_stop":
                        break

                if sentence_buffer:
                    await process_sentence(sentence_buffer)

                if self.text_output_enabled:
                    print(Style.RESET_ALL)

                if self.show_tokens:
                    output_tokens = await self.count_tokens(full_response)
                    total_tokens = input_tokens + output_tokens
                    print(f"{Fore.CYAN}Output tokens: {output_tokens}")
                    print(f"Total tokens: {total_tokens}{Style.RESET_ALL}")

                self.history.append({"role": "user", "content": message})
                self.history.append({"role": "assistant", "content": full_response})
                self.save_history()

                # Wait for audio playback to complete
                self.audio_queue.join()

                return

            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Max retries reached. Error: {str(e)}")
                    raise
                delay = base_delay * (2 ** attempt)
                logging.warning(f"API error occurred. Retrying in {delay} seconds...")
                await asyncio.sleep(delay)

    async def display_history(self):
        for entry in self.history:
            role = entry["role"].capitalize()
            content = entry["content"]
            color = Fore.YELLOW if role == "User" else Fore.GREEN
            print(f"{color}{role}: {content}{Style.RESET_ALL}")
            if self.show_tokens:
                tokens = await self.count_tokens(content)
                print(f"{Fore.CYAN}Tokens: {tokens}{Style.RESET_ALL}")
            print()

    def clear_history(self):
        self.backup_history()
        self.history = []
        self.save_history()
        print(f"{Fore.MAGENTA}Conversation history cleared and backed up.{Style.RESET_ALL}")

    def display_system_prompt(self):
        print(f"{Fore.CYAN}Current system prompt: {self.system_prompt}{Style.RESET_ALL}")

    def display_model(self):
        print(f"{Fore.CYAN}Current model: {self.model}")
        print(f"Max tokens: {self.max_tokens}")
        print(f"Log level: {logging.getLogger().level}{Style.RESET_ALL}")

    def toggle_tokens(self):
        self.show_tokens = not self.show_tokens
        status = "on" if self.show_tokens else "off"
        print(f"{Fore.MAGENTA}Token display is now {status}.{Style.RESET_ALL}")

    def toggle_speech(self):
        self.speech_enabled = not self.speech_enabled
        status = "on" if self.speech_enabled else "off"
        print(f"{Fore.MAGENTA}Speech output is now {status}.{Style.RESET_ALL}")

    def toggle_text_output(self):
        self.text_output_enabled = not self.text_output_enabled
        status = "on" if self.text_output_enabled else "off"
        print(f"{Fore.MAGENTA}Text output is now {status}.{Style.RESET_ALL}")

    def display_help(self):
        print(f"{Fore.CYAN}Available commands:")
        print("  exit    - Quit the application")
        print("  system  - Display the current system prompt")
        print("  history - Show the conversation history")
        print("  model   - Display the current Claude model being used")
        print("  clear   - Clear the conversation history (creates a backup)")
        print("  tokens  - Toggle the display of token counts")
        print("  speech  - Toggle speech output")
        print("  text    - Toggle text output")
        print(f"  help    - Display this help message{Style.RESET_ALL}")

    async def run(self):
        print(f"{Fore.MAGENTA}Welcome to the Claude CLI. Type 'help' for available commands or 'exit' to quit.{Style.RESET_ALL}")
        while True:
            user_input = input(f"{Fore.YELLOW}You: {Style.RESET_ALL}").strip()

            if user_input.lower() == 'exit':
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
            elif user_input.lower() == 'help':
                self.display_help()
            else:
                await self.send_message(user_input)

    def shutdown(self):
        self.audio_queue.put(None)  # Signal the audio thread to stop
        self.audio_thread.join()  # Wait for the audio thread to finish

if __name__ == "__main__":
    cli = ClaudeCLI()
    try:
        asyncio.run(cli.run())
    finally:
        cli.shutdown()