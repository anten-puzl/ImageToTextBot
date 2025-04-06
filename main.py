import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
import io
from PIL import Image

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message and language selection buttons."""
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Пожалуйста, выберите язык распознавания:", reply_markup=reply_markup)
    context.user_data['language'] = None  # Initialize language in user data

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets the language for OCR based on user selection."""
    query = update.callback_query
    await query.answer()
    language_code = query.data.split('_')[1]
    context.user_data['language'] = language_code
    language_name = "английский" if language_code == "en" else "русский"
    await query.edit_message_text(f"Вы выбрали {language_name} язык для распознавания. Теперь отправьте изображение.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming image messages and performs OCR with the selected language."""
    if update.message.photo:
        language = context.user_data.get('language')
        if language is None:
            await update.message.reply_text("Пожалуйста, сначала выберите язык распознавания, используя команду /start.")
            return

        try:
            # Get the largest available photo size
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            image_bytes = await file.download_as_bytearray()

            # Create a file-like object from the byte array
            img_stream = io.BytesIO(image_bytes)

            # Call Azure AI Vision for OCR with the selected language
            read_response = computervision_client.recognize_printed_text_in_stream(img_stream, language=language)

            text_lines = []
            if read_response.regions:
                for region in read_response.regions:
                    for line in region.lines:
                        text_lines.append(" ".join([word.text for word in line.words]))

            if text_lines:
                extracted_text = "\n".join(text_lines)
                response_text = "Recognized text (English):\n" if language == "en" else "Распознанный текст (русский):\n"
                await update.message.reply_text(response_text + extracted_text)
            else:
                response_not_found = "No text found in the image (English)." if language == "en" else "Текст на изображении не найден (русский)."
                await update.message.reply_text(response_not_found)

        except Exception as e:
            error_message = f"Error processing image (English): {e}" if language == "en" else f"Произошла ошибка при обработке изображения (русский): {e}"
            await update.message.reply_text(error_message)
    else:
        await update.message.reply_text("Please send an image.")

def main():
    # Initialize the bot with the token
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Command handler for starting the bot and selecting language
    application.add_handler(MessageHandler(filters.Command("start"), start))

    # Callback query handler for language selection
    application.add_handler(CallbackQueryHandler(set_language, pattern='^lang_'))

    # Handle image messages
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Start polling for updates
    application.run_polling()
    print("✅ Bot is running and listening for images.")

if __name__ == '__main__':
    main()