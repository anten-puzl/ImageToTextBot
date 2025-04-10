# main.py
import asyncio
import logging
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from core.config import TELEGRAM_TOKEN
from telegram_bot.handlers import start, button_click, handle_image, handle_version_text
from health_check.server import run_health_check_server

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

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