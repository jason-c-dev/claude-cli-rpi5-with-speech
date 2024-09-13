import os
import json
import asyncio
import re
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from colorama import init, Fore, Style

class ClaudeAPIManager:
    def __init__(self, config_manager, log_manager):
        self.config_manager = config_manager
        self.logger = log_manager.get_logger()
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = self.config_manager.get_model()
        self.max_tokens = self.config_manager.get_max_tokens()
        self.system_prompt = self.load_system_prompt()

    def load_system_prompt(self):
        system_prompt_file = self.config_manager.get_system_prompt_file()
        try:
            with open(system_prompt_file, "r", encoding='utf-8') as f:
                system_prompt = f.read().strip()
            self.logger.info("System prompt loaded successfully")
            return system_prompt
        except FileNotFoundError:
            self.logger.error(f"{system_prompt_file} not found. Using default system prompt.")
            return "You are a helpful AI assistant."
        except Exception as e:
            self.logger.error(f"Error loading system prompt: {str(e)}. Using default system prompt.")
            return "You are a helpful AI assistant."

    async def count_tokens(self, text):
        token_count = await self.client.count_tokens(text)
        self.logger.debug(f"Token count: {token_count}")
        return token_count

    async def send_message(self, message, history, speech_enabled, text_output_enabled, show_tokens, audio_manager):
        max_retries = 5
        base_delay = 1
        sequence_number = 0

        async def process_sentence(sentence):
            nonlocal sequence_number
            if speech_enabled and sentence.strip():
                file_path = await audio_manager.text_to_speech(sentence.strip(), sequence_number)
                if file_path:
                    audio_manager.queue_audio(file_path)
                    sequence_number += 1

        messages = self.format_messages(message, history)
        input_tokens = await self.count_tokens(json.dumps(messages) + self.system_prompt)
        
        if show_tokens:
            print(f"{Fore.CYAN}Input tokens: {input_tokens}{Style.RESET_ALL}")
        self.logger.info(f"Sending message to Claude. Input tokens: {input_tokens}")

        for attempt in range(max_retries):
            try:
                stream = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=messages,
                    system=self.system_prompt,
                    stream=True
                )

                full_response = ""
                sentence_buffer = ""
                if text_output_enabled:
                    print(f"{Fore.GREEN}Claude: ", end='', flush=True)

                async for chunk in stream:
                    if chunk.type == "content_block_delta":
                        if chunk.delta.text:
                            if text_output_enabled:
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

                if text_output_enabled:
                    print(Style.RESET_ALL)

                if show_tokens:
                    output_tokens = await self.count_tokens(full_response)
                    total_tokens = input_tokens + output_tokens
                    print(f"{Fore.CYAN}Output tokens: {output_tokens}")
                    print(f"Total tokens: {total_tokens}{Style.RESET_ALL}")
                    self.logger.info(f"Response received. Output tokens: {output_tokens}, Total tokens: {total_tokens}")

                # Wait for audio playback to complete
                audio_manager.wait_for_audio_completion()
                self.logger.info("Message sent and response processed successfully")

                return full_response

            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"Max retries reached. Error: {str(e)}")
                    raise
                delay = base_delay * (2 ** attempt)
                self.logger.warning(f"API error occurred. Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)

    def format_messages(self, message, history):
        # Only include the last 10 messages to prevent the context from growing too large
        recent_history = history[-10:] if len(history) > 10 else history
        formatted_messages = [{"role": entry["role"], "content": entry["content"]} for entry in recent_history]
        formatted_messages.append({"role": "user", "content": message})
        return formatted_messages