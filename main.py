import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, filters

# Load environment variables from .env file
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def handle_message(update, context):
    # Respond with "hello" to any text message
    await update.message.reply_text("hello2")

def main():
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN not found. Check your .env file.")
        return

    # Initialize the bot with the token
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Handle all text messages (excluding commands)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling for updates
    application.run_polling()
    print("✅ Bot is running.")

if __name__ == '__main__':
    main()
