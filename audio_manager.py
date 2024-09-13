import os
import threading
from queue import Queue
import logging
import tempfile
import uuid
from dotenv import load_dotenv
from colorama import init, Fore, Style
from botocore.exceptions import BotoCoreError, ClientError
import pygame

class AudioManager:
    def __init__(self, config_manager, polly_client):
        self.config_manager = config_manager
        self.polly_client = polly_client
        self.audio_queue = Queue()
        self.audio_thread = threading.Thread(target=self.audio_player_thread, daemon=True)
        self.audio_thread.start()
        self.aws_polly_voice = self.config_manager.get_aws_polly_voice()
        self.aws_polly_engine = self.config_manager.get_aws_polly_engine()

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

    def queue_audio(self, audio_file):
        self.audio_queue.put(audio_file)

    def wait_for_audio_completion(self):
        self.audio_queue.join()

    def shutdown(self):
        self.audio_queue.put(None)  # Signal the audio thread to stop
        self.audio_thread.join()  # Wait for the audio thread to finish