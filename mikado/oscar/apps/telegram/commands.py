import asyncio
from asgiref.sync import sync_to_async, async_to_sync

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder

from django.db.models import Q
from oscar.core.compat import get_user_model
from oscar.core.loading import get_model

from django.conf import settings
BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Логирование
# logger = logging.getLogger("TELEGRAM")
# logger.setLevel(logging.INFO)
# handler = logging.StreamHandler()
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)

# logging.getLogger("TELEGRAM").
# logging.getLogger("TELEGRAM").setLevel(logging.INFO).Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


TelegramStaff = get_model("telegram", "TelegramStaff")
User = get_user_model()


# =============  Команды  =================


# Функция для команды /start, которая запрашивает номер телефона
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton(text="Подписаться на уведомления", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Пожалуйста, отправьте ваш номер телефона для подписки на уведомелния Микадо:", reply_markup=reply_markup)


# =============  Обработчики  =================


# Обработчик для получения номера телефона
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.message.contact
    if contact:
        phone_number = contact.phone_number
        user_id = update.message.from_user.id
        try:
            # Проверяем, существует ли администратор с данным номером
            await link_telegram_to_user(phone_number, user_id)
            await update.message.reply_text("Вы успешно подписались на уведомления.")
        except User.DoesNotExist:
            await update.message.reply_text("Ваш номер телефона не найден в базе данных или вы не являетесь сотрудником. Обратитесь к администратору.")
    else:
        await update.message.reply_text("Ошибка при получении номера телефона.")

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


# =============  Вспомогательные функции  =================


@sync_to_async
def link_telegram_to_user(phone_number, user_id):
    user = User.objects.filter(Q(is_staff=True) | Q(groups__isnull=False)).get(username=phone_number)
    user.telegram_id = user_id
    user.save()
    telegram_staff, created = TelegramStaff.objects.get_or_create(user=user)
    telegram_staff.telegram_id = user_id
    telegram_staff.type = "error"
    telegram_staff.save()

def get_staffs():
    return TelegramStaff.objects.all()


# =============  Фукции Телеграм  =================


# Функция для отправки уведомления администраторам асинхроно
async def async_send_telegram_message_to_users(text, users=None):
    if users is None:
        users = await sync_to_async(get_staffs)()
    for user in users:
        try:
            await application.bot.send_message(chat_id=user.telegram_id, text=text)
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления: {e}")

# Функция для отправки уведомления администраторам синхронно
def send_telegram_message_to_users(text, users=None):
    if users is None:
        users = get_staffs()
    for user in users:
        try:
            # loop = asyncio.get_event_loop()
            # if loop.is_closed():
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            async_to_sync(application.bot.send_message)(chat_id=user.telegram_id, text=text)
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления: {e}")


# =============  Привязка команд к боту  =================


def link_comands(application):
    # Обработчик команды /start
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # Обработчик для получения контакта
    contact_handler = MessageHandler(filters.CONTACT, contact)
    application.add_handler(contact_handler)
