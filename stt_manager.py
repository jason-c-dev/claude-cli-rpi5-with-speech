import os
import json
import asyncio
import threading
from queue import Queue
import sounddevice as sd
import websockets
from websockets.exceptions import WebSocketException, ConnectionClosedError, ConnectionClosedOK
from dotenv import load_dotenv
from colorama import init, Fore, Style


class STTManager:
    def __init__(self, config_manager, log_manager):
        self.config_manager = config_manager
        self.logger = log_manager.get_logger()
        self.deepgram_model = self.config_manager.get_deepgram_model()
        self.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        self.stt_sample_rate = 16000
        self.stt_chunk_size = 1024
        self.stt_audio_queue = Queue()
        self.stop_audio = threading.Event()

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
                        self.logger.error(f"Error closing WebSocket: {str(e)}")

                if result and result.strip():
                    return result
                else:
                    print(f"{Fore.YELLOW}No speech detected. Please try again.{Style.RESET_ALL}")
                    return None

        except WebSocketException as e:
            print(f"{Fore.RED}WebSocket connection error: {str(e)}{Style.RESET_ALL}")
            self.logger.error(f"WebSocket connection error: {str(e)}")
        except ConnectionClosedError as e:
            if e.code == 1000:
                print(f"{Fore.CYAN}WebSocket connection closed normally.{Style.RESET_ALL}")
                self.logger.info("WebSocket connection closed normally.")
            else:
                print(f"{Fore.RED}WebSocket connection closed unexpectedly: {str(e)}{Style.RESET_ALL}")
                self.logger.error(f"WebSocket connection closed unexpectedly: {str(e)}")
        except ConnectionClosedOK:
            print(f"{Fore.CYAN}WebSocket connection closed gracefully.{Style.RESET_ALL}")
            self.logger.info("WebSocket connection closed gracefully.")
        except Exception as e:
            print(f"{Fore.RED}An unexpected error occurred: {str(e)}{Style.RESET_ALL}")
            self.logger.error(f"An unexpected error occurred: {str(e)}")
        finally:
            print(f"{Fore.CYAN}Disconnected from Deepgram.{Style.RESET_ALL}")

    def audio_capture_thread(self):
        def audio_callback(indata, frames, time, status):
            if status:
                self.logger.warning(f"Audio callback status: {status}")
            self.stt_audio_queue.put(indata.tobytes())

        try:
            with sd.InputStream(samplerate=self.stt_sample_rate, channels=1, dtype='int16', callback=audio_callback, blocksize=self.stt_chunk_size):
                while not self.stop_audio.is_set():
                    sd.sleep(100)
        except Exception as e:
            self.logger.error(f"Error in audio capture thread: {str(e)}")

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
                    self.logger.error(f"Error sending audio data: {str(e)}")
                    break
        except Exception as e:
            self.logger.error(f"Error in audio sender: {str(e)}")
        finally:
            try:
                await ws.send(json.dumps({"type": "CloseStream"}))
                self.logger.info("Sent CloseStream message")
            except ConnectionClosedOK:
                self.logger.info("WebSocket already closed gracefully")
            except ConnectionClosedError as e:
                if e.code == 1000:
                    self.logger.info("WebSocket closed normally")
                else:
                    self.logger.error(f"Error closing WebSocket: {str(e)}")
            except Exception as e:
                self.logger.error(f"Unexpected error while closing WebSocket: {str(e)}")

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
            self.logger.error(f"Error in audio receiver: {str(e)}")
        return transcript