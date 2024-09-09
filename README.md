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

## Technical Details

### Code Structure

The main `ClaudeCLI` class handles all functionality, including:
- Initialization and configuration loading
- Conversation management
- API interactions with Claude AI
- Text-to-speech conversion and audio playback
- Command processing and user interface

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
- Review the application logs for any error messages.

For further assistance, please open an issue in this repository.

## AI Assistance in Development

This project was developed with significant assistance from Claude 3.5 Sonnet, an AI model created by Anthropic. Claude provided guidance, code suggestions, and helped refine the implementation throughout the development process. This collaboration showcases the potential of AI-assisted coding in creating complex, functional applications.

### How Claude Assisted

- Provided initial code structure and implementation details
- Helped debug and optimize the code
- Offered suggestions for improving functionality and user experience
- Assisted in writing and formatting documentation, including this README

### Example Prompts Used

Here are some example prompts that were used during the development process:

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