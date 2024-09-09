# Claude CLI for Raspberry Pi 5

This project implements an advanced Command Line Interface (CLI) for interacting with Anthropic's Claude AI on a Raspberry Pi 5 running Ubuntu. It features real-time text and speech output, conversation history management, and various customization options.

## Features

- Interactive conversations with Claude AI
- Real-time text output
- Text-to-speech functionality using AWS Polly
- Conversation history management with JSON formatting
- Token usage tracking
- Toggleable speech and text output
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
   ```

   To obtain an Anthropic API key:
   - Visit the [Anthropic website](https://www.anthropic.com) and sign up for an account.
   - Navigate to the API section in your account settings.
   - Generate a new API key and copy it.
   - Never share your API key publicly or commit it to version control.

6. Create or update the `config.json` file in the project directory with your desired configuration:
   ```json
   {
     "system_prompt": "You are a helpful AI assistant.",
     "model": "claude-3-sonnet-20240229",
     "max_tokens": 4096,
     "log_level": "INFO",
     "speech_enabled": true,
     "text_output_enabled": true,
     "aws_polly_voice": "Ruth",
     "aws_polly_engine": "neural"
   }
   ```

7. Ensure that your Raspberry Pi is set up for audio output. If you're using HDMI for audio, you might need to force HDMI audio by adding the following line to `/boot/config.txt`:
   ```
   hdmi_drive=2
   ```

## Usage

Run the CLI application:
```
python3 claude-cli-rpi.py
```

### Available Commands:

- `exit`: Quit the application
- `system`: Display the current system prompt
- `history`: Show the conversation history
- `model`: Display the current Claude model being used
- `clear`: Clear the conversation history (creates a backup)
- `tokens`: Toggle the display of token counts
- `speech`: Toggle speech output
- `text`: Toggle text output
- `help`: Display available commands

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
├── .env
└── README.md
```

- The `logs` directory contains all log-related files:
  - `claude_cli.log`: The current log file
  - `claude_cli.log.1`, `claude_cli.log.2`, etc.: Rotated log files
  - `history.json`: The current conversation history
  - `history_backup_YYYYMMDD_HHMMSS.json`: Backup files of the conversation history

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

## Technical Details

### Code Structure

The main `ClaudeCLI` class handles all functionality, including:
- Initialization and configuration loading
- Conversation management
- API interactions with Claude AI
- Text-to-speech conversion and audio playback
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

### Error Handling

- The application includes retry logic for API calls to handle temporary network issues.
- Logging is implemented to track errors and application state.

## Notes

- Ensure proper cooling for your Raspberry Pi 5 during extended use.
- Maintain a stable internet connection for API communication.
- The conversation history is automatically saved and can be cleared or displayed using the appropriate commands.

## Troubleshooting

If you encounter any issues, please check the following:
- Ensure your Anthropic and AWS API keys are correct in the `.env` file.
- Verify that you have a stable internet connection.
- Check the `config.json` file for any syntax errors.
- Review the application logs in the `logs` directory for any error messages.

For further assistance, please open an issue in this repository.

## Contributing

Contributions to improve the Claude CLI are welcome. Please feel free to submit pull requests or open issues for bugs and feature requests.

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