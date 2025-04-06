import os
from dotenv import load_dotenv
from telegram.ext import Updater, MessageHandler, Filters
#comment1
# Load environment variables from .env file
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def handle_message(update, context):
    # Respond with "hello" to any text message
    update.message.reply_text("hello")

def main():
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN not found. Check your .env file.")
        return

    # Initialize the bot with the token
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Handle all text messages (excluding commands)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start polling for updates
    updater.start_polling()
    print("✅ Bot is running.")
    updater.idle()

if __name__ == '__main__':
    main()
