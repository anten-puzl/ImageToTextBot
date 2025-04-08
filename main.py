import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
import io
from azure.core.exceptions import ServiceRequestError
import asyncio
from aiohttp import web
import logging

# Load environment variables from .env file
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUBSCRIPTION_KEY = os.getenv("AiAzureToken")
ENDPOINT = os.getenv("AiAzureEndPoint")
HEALTH_CHECK_PORT = int(os.getenv("HEALTH_CHECK_PORT", 8000 ))

# Check if required environment variables are set
if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_TOKEN not found. Check your .env file.")
    exit()
if not SUBSCRIPTION_KEY or not ENDPOINT:
    print("❌ AiAzureToken or AiAzureEndPoint not found in .env file.")
    exit()

# Initialize Computer Vision client
computervision_client = ComputerVisionClient(ENDPOINT, CognitiveServicesCredentials(SUBSCRIPTION_KEY))

# Define the application version
APP_VERSION = "1.01"

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_image_with_retry(img_stream: io.BytesIO, language_hints=["en", "ru"], max_retries=3, retry_delay=2):
    """Analyzes the image with retry logic using asyncio."""
    try:
        # Read bytes once to avoid stream issues in to_thread
        image_bytes_data = img_stream.getvalue()
        if not image_bytes_data:
            raise ValueError("Empty image data received")

        for attempt in range(max_retries):
            try:
                # Create a new stream for each attempt and seek to start
                current_stream = io.BytesIO(image_bytes_data)
                current_stream.seek(0)
                
                # Run the blocking SDK call in a separate thread
                read_response = await asyncio.to_thread(
                    computervision_client.recognize_printed_text_in_stream,
                    current_stream,
                    language_hints=language_hints
                )
                
                if not read_response:
                    raise ValueError("Empty response from Azure API")
                    
                return read_response
            except ServiceRequestError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Temporary connection error (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Error after {max_retries} retries: {e}")
                    raise
            except Exception as e:
                logger.exception(f"An unexpected error occurred during image analysis: {e}")
                raise
    except Exception as e:
        logger.exception(f"Failed to process image: {e}")
        raise
    finally:
        try:
            img_stream.close()
        except:
            pass

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
                if len(extracted_text) > 4000:
                    chunks = [extracted_text[i:i+4000] for i in range(0, len(extracted_text), 4000)]
                    for chunk in chunks:
                        await update.message.reply_text(chunk.strip())
                else:
                    await update.message.reply_text(extracted_text.strip())
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

async def health_check(request):
    """Simple health check endpoint."""
    logger.debug("Health check requested")
    return web.Response(text="OK", status=200)

async def run_health_check_server():
    """Runs the aiohttp server for health checks."""
    app = web.Application()
    app.add_routes([
        web.get('/', health_check),
        web.get('/health', health_check)
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', HEALTH_CHECK_PORT)
    try:
        await site.start()
        logger.info(f"✅ Health check server started on http://0.0.0.0:{HEALTH_CHECK_PORT}/health")
        return runner
    except OSError as e:
        logger.error(f"❌ Failed to start health check server on port {HEALTH_CHECK_PORT}: {e}")
        return None

async def main():
    """Runs both the Telegram bot and the health check server concurrently."""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_version_text))

    # Start the health check server
    health_check_runner = await run_health_check_server()

    logger.info("Starting bot polling and health check server...")

    try:
        # Initialize the application
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        logger.info("✅ Bot and health check server started successfully.")

        # Keep the application running
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour
            
    except Exception as e:
        logger.exception("An error occurred in the main loop:")
    finally:
        logger.info("Shutting down application...")
        if application.updater and application.updater.is_running:
            await application.updater.stop()
        await application.stop()
        await application.shutdown()
        
        if health_check_runner:
            await health_check_runner.cleanup()
        logger.info("Application shutdown complete.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
    except Exception as e:
        logger.critical(f"Critical error during top-level execution: {e}", exc_info=True)
