# telegram_bot/handlers.py
import io
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from core.utils import analyze_image_with_retry, split_long_message
from core.config import APP_VERSION
from azure.core.exceptions import ServiceRequestError  # Добавьте этот импорт

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message with an inline button."""
    keyboard = [
        [InlineKeyboardButton("ℹ️ Version", callback_data='app_version')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Send an image to recognize text.", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the inline button click."""
    query = update.callback_query
    await query.answer()
    if query.data == 'app_version':
        await query.message.reply_text(f"Current application version: {APP_VERSION}")

async def handle_version_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'version' text message."""
    if update.message and update.message.text and update.message.text.lower() == "version":
        await update.message.reply_text(f"Current application version: {APP_VERSION}")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming image messages and performs OCR."""
    if not update.message or not update.message.photo:
        await update.message.reply_text("Please send an image.")
        return

    try:
        # Get the largest available photo size
        photo = update.message.photo[-1]
        logger.info(f"Processing image from user {update.message.from_user.id}, file_id: {photo.file_id}")

        # Send "processing" message
        processing_message = await update.message.reply_text("⏳ Processing image...")

        file = await context.bot.get_file(photo.file_id)
        # Download into memory as bytes
        image_bytes = await file.download_as_bytearray()

        if not image_bytes:
            raise ValueError("Failed to download image")

        # Create BytesIO from the downloaded bytes and ensure it's at the start
        img_stream = io.BytesIO(image_bytes)
        img_stream.seek(0)

        # Analyze the image with retry logic
        read_response = await analyze_image_with_retry(img_stream, language_hints=["en", "ru"])

        # Delete processing message
        await processing_message.delete()

        if read_response and read_response.regions:
            extracted_text = ""
            for region in read_response.regions:
                for line in region.lines:
                    extracted_text += " ".join([word.text for word in line.words]) + "\n"

            if extracted_text.strip():
                # Split long messages if needed (Telegram has a 4096 character limit)
                for chunk in split_long_message(extracted_text.strip()):
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text("❌ No text found in the image.")
        elif read_response:
            await update.message.reply_text("❌ Could not find any text regions in the image.")
        else:
            await update.message.reply_text("❌ Failed to recognize text after multiple attempts.")

    except ServiceRequestError as e:
        logger.error(f"Azure Service Request Error: {e}")
        await update.message.reply_text("❌ Error contacting the analysis service. Please try again later.")
    except ValueError as e:
        logger.error(f"Value Error: {e}")
        await update.message.reply_text(f"❌ {str(e)}")
    except Exception as e:
        logger.exception("Error processing image:")
        await update.message.reply_text("❌ An unexpected error occurred while processing the image.")
    finally:
        try:
            img_stream.close()
        except:
            pass