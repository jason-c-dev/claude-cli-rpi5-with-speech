# Claude CLI for Raspberry Pi 5

This project implements an advanced Command Line Interface (CLI) for interacting with Anthropic's Claude AI on a Raspberry Pi 5 running Ubuntu. It features real-time text and speech input/output, conversation history management, and various customization options.

## Features

- Interactive conversations with Claude AI
- Real-time text output
- Text-to-speech functionality using AWS Polly
- Speech-to-text functionality using Deepgram API
- Conversation history management with JSON formatting
- Token usage tracking
- Toggleable speech input/output and text output
- Customizable system prompt and model selection
- Error handling and automatic retries for API calls
- Centralized logging with log rotation

## Prerequisites

- Raspberry Pi 5 running Ubuntu
- Python 3.7 or later
- pip (Python package installer)
- Anthropic API key for accessing Claude AI
- AWS account for Polly text-to-speech service
- AWS API key and secret for accessing AWS services
- Deepgram API key for speech-to-text functionality
- Microphone/speaker connected to the Raspberry Pi (see Hardware Setup for specific recommendation)

## Hardware Setup

For optimal audio performance, this project was developed and tested using the following speaker/microphone:

- **M4 Bluetooth Speakerphone Conference Microphone**
  - Features: AI Noise Reduction, Full-Duplex, AI Transcription
  - 360° Voice Pickup
  - USB Connectivity
  - Compatible with Teams/Zoom
  - Color: Black
  - Available on Amazon: [M4 Bluetooth Speakerphone](https://www.amazon.com/AISPEECH-Speakerphone-Conference-Full-Duplex-Transcription/dp/B0CCP1J8QW?th=1)

This speakerphone provides excellent audio quality for both input (speech recognition) and output (text-to-speech playback). Its noise reduction and 360° voice pickup features are particularly useful for clear voice input in various environments.

While other microphones and speakers may work, using this or a similar high-quality conference speakerphone is recommended for the best experience with the Claude CLI.

## Third-Party Services

### Anthropic

Anthropic is the company behind Claude, the AI model used in this project. 

- Website: [https://www.anthropic.com](https://www.anthropic.com)
- SDK: The project uses the `anthropic` Python package. You can install it via pip:
  ```
  pip install anthropic
  ```
- Documentation: [Anthropic API Documentation](https://docs.anthropic.com/)
- User Guide: For detailed information on using Claude and the Anthropic API, refer to their [Getting Started Guide](https://docs.anthropic.com/claude/docs/getting-started-with-claude)

### Deepgram

Deepgram provides the speech-to-text functionality for this project.

- Website: [https://deepgram.com](https://deepgram.com)
- SDK: While this project uses Deepgram's WebSocket API directly, they also offer a Python SDK:
  ```
  pip install deepgram-sdk
  ```
- Documentation: [Deepgram API Documentation](https://developers.deepgram.com/docs)
- User Guide: For more information on using Deepgram's speech recognition capabilities, check out their [Python SDK Guide](https://developers.deepgram.com/docs/python-sdk)

## Audio Setup for Raspberry Pi

Before running the application, you need to set up the audio input and output on your Raspberry Pi. Follow these steps:

1. Update your package list:
   ```
   sudo apt-get update
   ```

2. Install PortAudio and other required development libraries:
   ```
   sudo apt-get install libportaudio2 libportaudiocpp0 portaudio19-dev
   ```

3. If you encounter any issues with audio, you might need to install additional audio-related packages:
   ```
   sudo apt-get install libasound-dev
   ```

4. After installing these libraries, reinstall the `sounddevice` Python package:
   ```
   pip install --upgrade sounddevice
   ```

5. If you're using HDMI for audio output, you might need to force HDMI audio. Edit the `/boot/config.txt` file:
   ```
   sudo nano /boot/config.txt
   ```
   Add the following line at the end of the file:
   ```
   hdmi_drive=2
   ```
   Save the file and exit the editor.

6. Reboot your Raspberry Pi to apply the changes:
   ```
   sudo reboot
   ```

7. After rebooting, test your audio input and output:
   - For audio output: `speaker-test -t wav`
   - For audio input: `arecord -d 5 test.wav` (records for 5 seconds), then `aplay test.wav` to play it back

If you encounter any issues with audio setup, consult the Raspberry Pi documentation or community forums for troubleshooting specific to your Pi model and OS version.

## Setup

1. Clone this repository or download the project files to your Raspberry Pi 5.

2. Navigate to the project directory:
   ```
   cd path/to/claude-cli
   ```

3. Create a virtual environment (optional but recommended):
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the project directory with your API keys:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   AWS_ACCESS_KEY_ID=your_aws_access_key_id
   AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
   AWS_REGION=your_preferred_aws_region
   DEEPGRAM_API_KEY=your_deepgram_api_key_here
   ```

6. Create or update the `config.json` file in the project directory with your desired configuration:
   ```json
   {
     "system_prompt_file": "system_prompt.txt",
     "model": "claude-3-5-sonnet-20240620",
     "temperature": 0.7,
     "top_p": 1,
     "max_tokens": 4096,
     "log_level": "INFO",
     "aws_polly_voice": "Ruth",
     "aws_polly_engine": "generative",
     "stt_enabled": false,
     "deepgram_model": "nova-2"
   }
   ```

7. Create a `system_prompt.txt` file in the project directory with your desired system prompt:
   ```
   You are a helpful AI assistant. (Add your custom system prompt here)
   ```

8. Ensure that your Raspberry Pi is set up for audio input and output. If you're using HDMI for audio output, you might need to force HDMI audio by adding the following line to `/boot/config.txt`:
   ```
   hdmi_drive=2
   ```

## Usage

Run the CLI application:
```
python3 claude-cli-rpi.py
```

### Available Commands:

- `exit`: Quit the application (can also say "goodbye" if using voice input)
- `system`: Display the current system prompt
- `history`: Show the conversation history
- `model`: Display the current Claude model being used
- `clear`: Clear the conversation history (creates a backup)
- `tokens`: Toggle the display of token counts
- `speech`: Toggle speech output
- `text`: Toggle text output
- `stt`: Toggle speech-to-text input
- `help`: Display available commands

### Voice Input

When speech-to-text is enabled, the application will listen for your voice input. You can speak your messages, and the application will transcribe them and send them to Claude. To exit the application using voice, simply say "goodbye".

## File Structure

After running the application, you'll see the following file structure:

```
your_project_directory/
├── logs/
│   ├── claude_cli.log
│   ├── claude_cli.log.1
│   ├── claude_cli.log.2
│   ├── ...
│   ├── history.json
│   └── history_backup_YYYYMMDD_HHMMSS.json
├── claude-cli-rpi.py
├── config.json
├── system_prompt.txt
├── .env
└── README.md
```

## Logging

The application uses a rotating file handler for logging, which helps manage log file sizes:

- Log files are stored in the `logs` directory.
- The main log file is named `claude_cli.log`.
- When a log file reaches 1 MB in size, it's rotated (renamed to `claude_cli.log.1`, etc.).
- Up to 5 rotated log files are kept before the oldest is deleted.
- The log level can be set in the `config.json` file (e.g., "INFO", "DEBUG", "WARNING").

## Conversation History

- The conversation history is stored in `logs/history.json`.
- Each time the history is cleared, a backup is created in the `logs` directory with a timestamp.
- The history can be viewed using the `history` command in the CLI.

## Customizing the System Prompt

To customize the system prompt:

1. Open the `system_prompt.txt` file in a text editor.
2. Modify the content to suit your needs. This prompt sets the behavior and context for Claude AI.
3. Save the file.

The application will automatically load the new system prompt on the next run.

## Technical Details

### Code Structure

The main `ClaudeCLI` class handles all functionality, including:
- Initialization and configuration loading
- Conversation management
- API interactions with Claude AI
- Text-to-speech conversion and audio playback
- Speech-to-text conversion using Deepgram API
- Command processing and user interface
- Logging and file management

### Threading

The application uses a separate thread for audio playback to prevent delays in the main conversation loop:
- The main thread handles user input, API calls, and text processing.
- A dedicated audio thread manages the queuing and playback of speech audio files.
- Communication between threads is handled via a thread-safe Queue.

### Text-to-Speech Processing

- Sentences are processed individually as they are received from the API.
- Each sentence is converted to speech using AWS Polly and saved as a temporary MP3 file.
- Audio files are queued for playback in the order they are created.

### Speech-to-Text Processing

- The application uses the Deepgram API for real-time speech recognition.
- When STT is enabled, the application listens for voice input using the connected microphone.
- Transcribed text is processed and sent to Claude AI for response.

### Error Handling

- The application includes retry logic for API calls to handle temporary network issues.
- Logging is implemented to track errors and application state.

## Notes

- Ensure proper cooling for your Raspberry Pi 5 during extended use.
- Maintain a stable internet connection for API communication.
- The conversation history is automatically saved and can be cleared or displayed using the appropriate commands.
- When using voice input, speak clearly and wait for the application to process your speech before continuing.

## Troubleshooting

If you encounter any issues, please check the following:
- Ensure your Anthropic, AWS, and Deepgram API keys are correct in the `.env` file.
- Verify that you have a stable internet connection.
- Check the `config.json` file for any syntax errors.
- Review the application logs in the `logs` directory for any error messages.
- If you're having issues with voice input:
  - Check your microphone connection and system audio settings.
  - Ensure you've completed all the steps in the Audio Setup section.
  - Run `arecord -l` to list audio input devices and make sure your microphone is recognized.
  - If using a USB microphone, try different USB ports.
  - Check the audio levels using `alsamixer` and ensure the microphone isn't muted.

For further assistance, please open an issue in this repository.

## Contributing

Contributions to improve the Claude CLI are welcome. Please feel free to submit pull requests or open issues for bugs and feature requests.

## AI Assistance in Development

This project was developed with significant assistance from Claude 3.5 Sonnet, an AI model created by Anthropic. Claude provided guidance, code suggestions, and helped refine the implementation throughout the development process. This collaboration showcases the potential of AI-assisted coding in creating complex, functional applications.

1. "Can you help me create a Python script to interact with the Claude API and implement a command-line interface?"
2. "I'd like to add speech capabilities using AWS Polly. How can I integrate this into the existing code?"
3. "The audio playback is experiencing delays. Can you suggest a way to implement threaded audio processing to improve performance?"
4. "How can I implement proper error handling and retries for API calls in this application?"
5. "Can you help me update the README to include all the latest functionality and details about the code, threading, etc.?"
These prompts led to detailed discussions and iterative improvements of the code and documentation. The responses from Claude were then reviewed, modified as needed, and integrated into the project.

### Benefits of AI-Assisted Development

- Rapid prototyping and implementation of complex features
- Access to a broad knowledge base for problem-solving
- Assistance in writing clear, well-structured documentation
- Ability to explore multiple approaches to solving problems

While Claude provided significant assistance, human oversight, decision-making, and final implementation were crucial in creating this functional and tailored application.

We encourage users and contributors to explore AI-assisted development in their own projects, as it can be a powerful tool for enhancing productivity and creativity in software development.

## License

MIT License
Copyright (c) 2024 Jason Croucher
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.