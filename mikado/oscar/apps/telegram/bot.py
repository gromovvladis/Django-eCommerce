# bot.py
import logging
from django.conf import settings
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup

# Инициализация Django
# import django
# import os
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evotor_sync.settings')
# django.setup()

from oscar.core.compat import get_user_model
User = get_user_model()

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


# Функция для команды /start, которая запрашивает номер телефона
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton(text="Отправить номер телефона", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Пожалуйста, отправьте ваш номер телефона для подтверждения:", reply_markup=reply_markup)


# Обработчик для получения номера телефона
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.message.contact
    if contact:
        phone_number = contact.phone_number
        user_id = update.message.from_user.id
        try:
            # Проверяем, существует ли администратор с данным номером
            admin = User.objects.get(phone_number=phone_number)
            admin.telegram_id = user_id
            admin.save()
            await update.message.reply_text("Вы успешно подписались на уведомления.")
        except User.DoesNotExist:
            await update.message.reply_text("Ваш номер телефона не найден в базе данных. Обратитесь к администратору.")
    else:
        await update.message.reply_text("Ошибка при получении номера телефона.")


# Функция для отправки уведомления администраторам
async def send_notification(text: str):
    admins = User.objects.exclude(telegram_id=None).filter(is_staff=True)
    for admin in admins:
        try:
            await application.bot.send_message(chat_id=admin.telegram_id, text=text)
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления: {e}")



# Основная функция для запуска бота
if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Обработчик команды /start
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # Обработчик для получения контакта
    contact_handler = MessageHandler(filters.CONTACT, contact_handler)
    application.add_handler(contact_handler)

    # Запуск бота
    application.run_polling()
