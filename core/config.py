# core/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUBSCRIPTION_KEY = os.getenv("AiAzureToken")
ENDPOINT = os.getenv("AiAzureEndPoint")
HEALTH_CHECK_PORT = int(os.getenv("PORT", 8000))

# Check if required environment variables are set
if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_TOKEN not found. Check your .env file.")
    exit()
if not SUBSCRIPTION_KEY or not ENDPOINT:
    print("❌ AiAzureToken or AiAzureEndPoint not found in .env file.")
    exit()

APP_VERSION = "1.01"