# orignal code created before refactor ** DO NOT USE FOLLOW README and run main.py **

import os
import json
import asyncio
import threading
from queue import Queue
import re
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import tempfile
import uuid
import sounddevice as sd
import numpy as np
import websockets
from websockets.exceptions import WebSocketException, ConnectionClosedError, ConnectionClosedOK
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from colorama import init, Fore, Style
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import pygame
import queue

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()

# Initialize pygame mixer
pygame.mixer.init()

class ClaudeCLI:
    def __init__(self):
        self.config = self.load_config()
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.setup_logging()
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.history = self.load_history()
        self.system_prompt = self.load_system_prompt()
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
        self.stt_enabled = self.config.get("stt_enabled", False)
        self.deepgram_model = self.config.get("deepgram_model", "general")
        self.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        self.stt_sample_rate = 16000
        self.stt_chunk_size = 1024
        self.stt_audio_queue = Queue()
        self.stop_audio = threading.Event()
        logging.info("ClaudeCLI initialized successfully")

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
            logging.info("Configuration loaded successfully")
            return config
        except FileNotFoundError:
            logging.warning("config.json not found. Using default configuration.")
            return {}
        except json.JSONDecodeError:
            logging.error("Error decoding config.json. Using default configuration.")
            return {}

    def load_system_prompt(self):
        system_prompt_file = self.config.get("system_prompt_file", "system_prompt.txt")
        try:
            with open(system_prompt_file, "r", encoding='utf-8') as f:
                system_prompt = f.read().strip()
            logging.info("System prompt loaded successfully")
            return system_prompt
        except FileNotFoundError:
            logging.error(f"{system_prompt_file} not found. Using default system prompt.")
            return "You are a helpful AI assistant."
        except Exception as e:
            logging.error(f"Error loading system prompt: {str(e)}. Using default system prompt.")
            return "You are a helpful AI assistant."

    def setup_logging(self):
        log_level_str = self.config.get("log_level", "INFO").upper()
        log_file = os.path.join(self.log_dir, "claude_cli.log")

        try:
            log_level = getattr(logging, log_level_str)
            
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

    def load_history(self):
        history_file = os.path.join(self.log_dir, "history.json")
        try:
            with open(history_file, "r", encoding='utf-8') as f:
                history = json.load(f)
            logging.info("Conversation history loaded successfully")
            return history
        except FileNotFoundError:
            logging.warning("history.json not found. Starting with empty history.")
            return []
        except json.JSONDecodeError:
            logging.error("Error decoding history.json. Starting with empty history.")
            return []

    def save_history(self):
        history_file = os.path.join(self.log_dir, "history.json")
        with open(history_file, "w", encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
        logging.info("Conversation history saved")

    def backup_history(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"history_backup_{timestamp}.json"
        backup_file = os.path.join(self.log_dir, backup_filename)
        with open(backup_file, "w", encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
        logging.info(f"Conversation history backed up to {backup_filename}")

    def clear_history(self):
        logging.info("Clearing conversation history")
        self.backup_history()
        self.history = []
        self.save_history()
        print(f"{Fore.MAGENTA}Conversation history cleared and backed up.{Style.RESET_ALL}")

    def format_messages(self, message):
        messages = self.history + [{"role": "user", "content": message}]
        return messages

    async def count_tokens(self, text):
        token_count = await self.client.count_tokens(text)
        logging.debug(f"Token count: {token_count}")
        return token_count

    def audio_player_thread(self):
        logging.info("Audio player thread started")
        while True:
            audio_file = self.audio_queue.get()
            if audio_file is None:  # None is our signal to stop
                logging.info("Audio player thread stopping")
                break
            logging.debug(f"Playing audio file: {audio_file}")
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            os.remove(audio_file)  # Clean up the file after playing
            logging.debug(f"Finished playing and removed audio file: {audio_file}")
            self.audio_queue.task_done()

    async def text_to_speech(self, text, sequence_number):
        try:
            logging.debug(f"Converting text to speech: '{text[:50]}...'")
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
                
                logging.debug(f"Speech file created: {file_path}")
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
                logging.info(f"Sending message to Claude. Input tokens: {input_tokens}")

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
                            
                            sentences = re.split(r'(?<!\d)(?<!\.\d)(\.|!|\?)\s+', sentence_buffer)
                            for i in range(0, len(sentences) - 1, 2):
                                sentence = sentences[i] + sentences[i+1]
                                await process_sentence(sentence)
                            
                            sentence_buffer = sentences[-1] if sentences else ""

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
                    logging.info(f"Response received. Output tokens: {output_tokens}, Total tokens: {total_tokens}")

                self.history.append({"role": "user", "content": message})
                self.history.append({"role": "assistant", "content": full_response})
                self.save_history()

                # Wait for audio playback to complete
                self.audio_queue.join()
                logging.info("Message sent and response processed successfully")

                return

            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Max retries reached. Error: {str(e)}")
                    raise
                delay = base_delay * (2 ** attempt)
                logging.warning(f"API error occurred. Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)

    async def display_history(self):
        logging.info("Displaying conversation history")
        for entry in self.history:
            role = entry["role"].capitalize()
            content = entry["content"]
            color = Fore.YELLOW if role == "User" else Fore.GREEN
            print(f"{color}{role}: {content}{Style.RESET_ALL}")
            if self.show_tokens:
                tokens = await self.count_tokens(content)
                print(f"{Fore.CYAN}Tokens: {tokens}{Style.RESET_ALL}")
            print()

    def display_system_prompt(self):
        logging.info("Displaying system prompt")
        print(f"{Fore.CYAN}Current system prompt:")
        print(f"{self.system_prompt}{Style.RESET_ALL}")

    def display_model(self):
        logging.info("Displaying model information")
        print(f"{Fore.CYAN}Current model: {self.model}")
        print(f"Max tokens: {self.max_tokens}")
        print(f"Log level: {logging.getLogger().level}{Style.RESET_ALL}")

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
        logging.info(f"Speech-to-Text toggled {status}")
        print(f"{Fore.MAGENTA}Speech-to-Text is now {status}.{Style.RESET_ALL}")

    async def listen_for_speech(self):
        print(f"{Fore.CYAN}Connecting to Deepgram, please wait...{Style.RESET_ALL}")

        deepgram_url = f"wss://api.deepgram.com/v1/listen?model={self.deepgram_model}&punctuate=true&encoding=linear16&sample_rate={self.stt_sample_rate}&endpointing=500"

        try:
            async with websockets.connect(deepgram_url, extra_headers={"Authorization": f"Token {self.deepgram_api_key}"}) as ws:
                print(f"{Fore.CYAN}Connected. Listening, now talk...{Style.RESET_ALL}")

                self.stop_audio.clear()  # Reset the stop event
                self.stt_audio_queue = Queue()  # Create a new queue for this session
                audio_thread = threading.Thread(target=self.audio_capture_thread)
                audio_thread.start()

                sender_task = asyncio.create_task(self.audio_sender(ws))
                receiver_task = asyncio.create_task(self.audio_receiver(ws))

                try:
                    done, pending = await asyncio.wait(
                        [sender_task, receiver_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    for task in pending:
                        task.cancel()
                    
                    result = next(iter(done)).result()
                finally:
                    self.stop_audio.set()
                    audio_thread.join()

                    # Ensure the WebSocket is closed properly
                    try:
                        await ws.close()
                    except Exception as e:
                        logging.error(f"Error closing WebSocket: {str(e)}")

                if result and result.strip():
                    return result
                else:
                    print(f"{Fore.YELLOW}No speech detected. Please try again.{Style.RESET_ALL}")
                    return None

        except WebSocketException as e:
            print(f"{Fore.RED}WebSocket connection error: {str(e)}{Style.RESET_ALL}")
            logging.error(f"WebSocket connection error: {str(e)}")
        except ConnectionClosedError as e:
            if e.code == 1000:
                print(f"{Fore.CYAN}WebSocket connection closed normally.{Style.RESET_ALL}")
                logging.info("WebSocket connection closed normally.")
            else:
                print(f"{Fore.RED}WebSocket connection closed unexpectedly: {str(e)}{Style.RESET_ALL}")
                logging.error(f"WebSocket connection closed unexpectedly: {str(e)}")
        except ConnectionClosedOK:
            print(f"{Fore.CYAN}WebSocket connection closed gracefully.{Style.RESET_ALL}")
            logging.info("WebSocket connection closed gracefully.")
        except Exception as e:
            print(f"{Fore.RED}An unexpected error occurred: {str(e)}{Style.RESET_ALL}")
            logging.error(f"An unexpected error occurred: {str(e)}")
        finally:
            print(f"{Fore.CYAN}Disconnected from Deepgram.{Style.RESET_ALL}")

    def audio_capture_thread(self):
        def audio_callback(indata, frames, time, status):
            if status:
                logging.warning(f"Audio callback status: {status}")
            self.stt_audio_queue.put(indata.tobytes())

        try:
            with sd.InputStream(samplerate=self.stt_sample_rate, channels=1, dtype='int16', callback=audio_callback, blocksize=self.stt_chunk_size):
                while not self.stop_audio.is_set():
                    sd.sleep(100)
        except Exception as e:
            logging.error(f"Error in audio capture thread: {str(e)}")

    async def audio_sender(self, ws):
        try:
            while not self.stop_audio.is_set():
                try:
                    audio_data = await asyncio.get_event_loop().run_in_executor(None, self.stt_audio_queue.get, True, 1.0)
                    await ws.send(audio_data)
                except asyncio.TimeoutError:
                    # No audio data received, but continue loop
                    continue
                except Exception as e:
                    logging.error(f"Error sending audio data: {str(e)}")
                    break
        except Exception as e:
            logging.error(f"Error in audio sender: {str(e)}")
        finally:
            try:
                await ws.send(json.dumps({"type": "CloseStream"}))
                logging.info("Sent CloseStream message")
            except ConnectionClosedOK:
                logging.info("WebSocket already closed gracefully")
            except ConnectionClosedError as e:
                if e.code == 1000:
                    logging.info("WebSocket closed normally")
                else:
                    logging.error(f"Error closing WebSocket: {str(e)}")
            except Exception as e:
                logging.error(f"Unexpected error while closing WebSocket: {str(e)}")

    async def audio_receiver(self, ws):
        transcript = ""
        try:
            async for msg in ws:
                res = json.loads(msg)
                if res.get("is_final"):
                    transcript = res.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                    if transcript.strip():
                        if "goodbye" in transcript.lower():
                            print(f"{Fore.MAGENTA}Goodbye detected. Exiting Claude CLI.{Style.RESET_ALL}")
                            return "GOODBYE_DETECTED"
                        return transcript.strip()
        except Exception as e:
            logging.error(f"Error in audio receiver: {str(e)}")
        return transcript
    
    async def run(self):
        logging.info("Starting Claude CLI")
        print(f"{Fore.MAGENTA}Welcome to the Claude CLI. Type 'help' for available commands or 'exit' to quit.{Style.RESET_ALL}")
        while True:
            if self.stt_enabled:
                try:
                    user_input = await self.listen_for_speech()
                    if user_input is None:
                        continue  # Skip this iteration and prompt for input again
                    if user_input == "GOODBYE_DETECTED":
                        logging.info("Exiting Claude CLI due to 'goodbye' detection")
                        break
                    print(f"{Fore.YELLOW}You: {user_input}{Style.RESET_ALL}")
                except Exception as e:
                    logging.error(f"Error in speech recognition: {str(e)}")
                    print(f"{Fore.RED}Speech recognition failed. Please type your input.{Style.RESET_ALL}")
                    user_input = input(f"{Fore.YELLOW}You: {Style.RESET_ALL}").strip()
            else:
                user_input = input(f"{Fore.YELLOW}You: {Style.RESET_ALL}").strip()

            if not user_input:
                continue  # Skip empty input

            logging.debug(f"User input: {user_input}")

            if user_input.lower() == 'exit':
                logging.info("Exiting Claude CLI")
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

    def shutdown(self):
        logging.info("Shutting down Claude CLI")
        self.stop_audio.set()
        self.audio_queue.put(None)  # Signal the audio thread to stop
        self.audio_thread.join()  # Wait for the audio thread to finish
        logging.info("Claude CLI shutdown complete")

if __name__ == "__main__":
    cli = ClaudeCLI()
    try:
        asyncio.run(cli.run())
    finally:
        cli.shutdown()