# telegram_bot/handlers.py
import io
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from core.utils import analyze_image_with_retry, split_long_message
from core.config import APP_VERSION, BOT_PASSWORD  # Импортируем BOT_PASSWORD
from azure.core.exceptions import ServiceRequestError

logger = logging.getLogger(__name__)

# Словарь для хранения статуса авторизации пользователей (user_id: is_authorized)
user_authorization = {}
CORRECT_PASSWORD = BOT_PASSWORD  # Используем пароль из config

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message and handles password entry."""
    user_id = update.effective_user.id
    if not CORRECT_PASSWORD:
        user_authorization[user_id] = True
        keyboard = [
            [InlineKeyboardButton("ℹ️ Версия", callback_data='app_version')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Добро пожаловать! Бот работает без пароля.", reply_markup=reply_markup)
        return 'AUTHORIZED'
    elif user_id not in user_authorization:
        await update.message.reply_text("Добро пожаловать! Пожалуйста, введите пароль для продолжения:")
        return 'WAITING_FOR_PASSWORD'
    elif user_authorization[user_id]:
        keyboard = [
            [InlineKeyboardButton("ℹ️ Версия", callback_data='app_version')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Вы авторизованы. Отправьте изображение для распознавания текста.", reply_markup=reply_markup)
        return 'AUTHORIZED'
    else:
        await update.message.reply_text("Неверный пароль. Работа бота остановлена.")
        return 'UNAUTHORIZED'

async def process_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes the entered password."""
    user_id = update.effective_user.id
    entered_password = update.message.text
    if entered_password == CORRECT_PASSWORD:
        user_authorization[user_id] = True
        keyboard = [
            [InlineKeyboardButton("ℹ️ Версия", callback_data='app_version')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Пароль принят. Вы авторизованы. Отправьте изображение для распознавания текста.", reply_markup=reply_markup)
        return 'AUTHORIZED'
    else:
        user_authorization[user_id] = False
        await update.message.reply_text("Неверный пароль. Пожалуйста, попробуйте еще раз, отправив /start.")
        return 'WAITING_FOR_PASSWORD'

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the inline button click."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if user_authorization.get(user_id, False):
        if query.data == 'app_version':
            await query.message.reply_text(f"Текущая версия приложения: {APP_VERSION}")
    else:
        await query.message.reply_text("Бот не авторизован. Пожалуйста, введите пароль, отправив /start.")

async def handle_version_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'version' text message."""
    user_id = update.effective_user.id
    if user_authorization.get(user_id, False):
        if update.message and update.message.text and update.message.text.lower() == "version":
            await update.message.reply_text(f"Текущая версия приложения: {APP_VERSION}")
    else:
        await update.message.reply_text("Бот не авторизован. Пожалуйста, введите пароль, отправив /start.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming image messages and performs OCR if authorized."""
    user_id = update.effective_user.id
    if user_authorization.get(user_id, False):
        if not update.message or not update.message.photo:
            await update.message.reply_text("Пожалуйста, отправьте изображение.")
            return

        try:
            # Get the largest available photo size
            photo = update.message.photo[-1]
            logger.info(f"Processing image from user {user_id}, file_id: {photo.file_id}")

            # Send "processing" message
            processing_message = await update.message.reply_text("⏳ Обработка изображения...")

            file = await context.bot.get_file(photo.file_id)
            # Download into memory as bytes
            image_bytes = await file.download_as_bytearray()

            if not image_bytes:
                raise ValueError("Не удалось скачать изображение")

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
                    await update.message.reply_text("❌ Текст на изображении не найден.")
            elif read_response:
                await update.message.reply_text("❌ Не удалось найти текстовые области на изображении.")
            else:
                await update.message.reply_text("❌ Не удалось распознать текст после нескольких попыток.")

        except ServiceRequestError as e:
            logger.error(f"Azure Service Request Error: {e}")
            await update.message.reply_text("❌ Ошибка при обращении к сервису анализа. Пожалуйста, попробуйте позже.")
        except ValueError as e:
            logger.error(f"Value Error: {e}")
            await update.message.reply_text(f"❌ {str(e)}")
        except Exception as e:
            logger.exception("Error processing image:")
            await update.message.reply_text("❌ Произошла непредвиденная ошибка при обработке изображения.")
        finally:
            try:
                img_stream.close()
            except:
                pass
    else:
        await update.message.reply_text("Бот не авторизован. Пожалуйста, введите пароль, отправив /start.")