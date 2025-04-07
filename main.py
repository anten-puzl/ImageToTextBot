import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
import io
import time
from azure.core.exceptions import ServiceRequestError

#1
# Load environment variables from .env file
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUBSCRIPTION_KEY = os.getenv("AiAzureToken")
ENDPOINT = os.getenv("AiAuzreEndPoint")

# Check if required environment variables are set
if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_TOKEN not found. Check your .env file.")
    exit()
if not SUBSCRIPTION_KEY or not ENDPOINT:
    print("❌ AiAzureToken or AiAuzreEndPoint not found in .env file.")
    exit()

# Initialize Computer Vision client
computervision_client = ComputerVisionClient(ENDPOINT, CognitiveServicesCredentials(SUBSCRIPTION_KEY))

# Define the application version
APP_VERSION = "1.01"

async def analyze_image_with_retry(img_stream: io.BytesIO, language_hints=["en", "ru"], max_retries=3, retry_delay=2):
    """Analyzes the image with retry logic."""
    for attempt in range(max_retries):
        try:
            read_response = computervision_client.recognize_printed_text_in_stream(img_stream, language_hints=language_hints)
            return read_response
        except ServiceRequestError as e:
            if attempt < max_retries - 1:
                print(f"Temporary connection error (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Error after {max_retries} retries: {e}")
                raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise
    return None

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming image messages and performs OCR."""
    if update.message.photo:
        try:
            # Get the largest available photo size
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            image_bytes = await file.download_as_bytearray()

            # Create a file-like object from the byte array
            img_stream = io.BytesIO(image_bytes)

            # Analyze image with retry logic
            read_response = await analyze_image_with_retry(img_stream, language_hints=["en", "ru"])

            if read_response:
                extracted_text = ""
                if read_response.regions:
                    for region in read_response.regions:
                        for line in region.lines:
                            extracted_text += " ".join([word.text for word in line.words]) + "\n"

                if extracted_text.strip():
                    await update.message.reply_text(extracted_text.strip())
                else:
                    await update.message.reply_text("No text found in the image.")
            else:
                await update.message.reply_text("Failed to recognize text after multiple attempts.")

        except ServiceRequestError as e:
            await update.message.reply_text(f"Error processing image (network issue): {e}")
        except Exception as e:
            await update.message.reply_text(f"Error processing image: {e}")
    else:
        await update.message.reply_text("Please send an image.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message with an inline button."""
    keyboard = [
        [InlineKeyboardButton("ℹ️ Версия", callback_data='app_version')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать! Отправьте изображение для распознавания текста.", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the inline button click."""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query
    if query.data == 'app_version':
        await query.message.reply_text(f"Текущая версия приложения: {APP_VERSION}")

async def handle_version_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'version' text message."""
    if update.message.text.lower() == "version":
        await update.message.reply_text(f"Текущая версия приложения: {APP_VERSION}")

def main():
    # Initialize the bot with the token
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Handle the /start command
    application.add_handler(CommandHandler("start", start))

    # Handle inline button clicks
    application.add_handler(CallbackQueryHandler(button_click))

    # Handle image messages
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Handle the 'version' text message
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_version_text))

    # Start polling for updates
    application.run_polling()
    print("✅ Bot is running and listening for images.")

if __name__ == '__main__':
    main()