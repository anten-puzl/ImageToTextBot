# ImageToTextBot

A Telegram bot that uses Azure Computer Vision to extract text from images.

## Overview

This Telegram bot allows users to send images and receive the extracted text. It leverages the power of Azure Computer Vision's Optical Character Recognition (OCR) service for accurate text extraction. The bot is built using the `python-telegram-bot` library for Telegram API interaction and the `azure-cognitiveservices-vision-computervision` library for communicating with Azure.

## Features

* **Image to Text Conversion:** Send any image to the bot, and it will attempt to extract the text content.
* **Language Hints:** Supports specifying language hints (English and Russian are currently configured) to improve OCR accuracy.
* **Retry Mechanism:** Implements a retry logic for the Azure API calls to handle temporary network issues.
* **Long Text Handling:** Automatically splits long extracted texts into multiple messages to comply with Telegram's message length limits.
* **Basic Welcome Message:** Greets users with a welcome message and a version information button.
* **Version Information:** Provides the current version of the bot via an inline button or by sending the text "version".
* **Health Check Endpoint:** Includes a simple web server for health checks, useful for monitoring the bot's status.

## Prerequisites

* **Python 3.6 or higher:** Ensure you have Python installed on your system.
* **Telegram Bot Token:** You need to create a Telegram bot and obtain its token from BotFather.
* **Azure Computer Vision Subscription Key and Endpoint:** You need an Azure account with a Computer Vision resource created to get the subscription key and endpoint.

## Installation

1.  **Clone the repository (if you have the code locally):**
    ```bash
    git clone <repository_url>
    cd ImageToTextBot
    ```

2.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```
    Alternatively, install them individually:
    ```bash
    pip install python-dotenv python-telegram-bot azure-cognitiveservices-vision aiohttp
    ```

3.  **Create a `.env` file in the root directory and add your Telegram Bot Token and Azure credentials:**
    ```
    TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
    AiAzureToken=YOUR_AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY
    AiAzureEndPoint=YOUR_AZURE_COMPUTER_VISION_ENDPOINT
    PORT=8000  # Optional, the port for the health check server (defaults to 8000)
    ```
    Replace `YOUR_TELEGRAM_BOT_TOKEN`, `YOUR_AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY`, and `YOUR_AZURE_COMPUTER_VISION_ENDPOINT` with your actual credentials.

## Running the Bot

1.  **Navigate to the root directory of the project.**
2.  **Run the `main.py` script:**
    ```bash
    python main.py
    ```

The bot will start polling for updates from Telegram, and the health check server will start on the specified port (default is `http://0.0.0.0:8000/health`).

## Project Structure

.
├── core/
│   ├── __init__.py
│   ├── azure_client.py     # Handles interaction with Azure Computer Vision API
│   ├── config.py           # Loads and manages application configuration
│   └── utils.py            # Contains utility functions (retry logic, text splitting)
├── health_check/
│   ├── __init__.py
│   └── server.py           # Implements a simple health check web server
├── telegram_bot/
│   ├── __init__.py
│   └── handlers.py         # Contains Telegram bot command and message handlers
├── __init__.py
├── .env                    # Stores environment variables (API keys, tokens)
├── .gitignore
├── main.py                 # Main entry point of the application
└── requirements.txt        # Lists the required Python packages


## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, feel free to open a pull request or submit an issue.

## License

MIT License

Copyright (c) 2025 Anton Pazulskyi

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