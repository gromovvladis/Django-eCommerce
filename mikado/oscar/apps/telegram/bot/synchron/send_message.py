import requests
from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

DEFAULT_BOT = settings.TELEGRAM_BOT_TOKEN

from oscar.core.loading import get_model
Staff = get_model("user", "Staff")
TelegramMassage = get_model("telegram", "TelegramMassage")

# Синхронная функция отправки сообщения через Telegram API
def send_message(chat_id: int, text: str, type: str = TelegramMassage.MISC, bot_token: str = DEFAULT_BOT,  **kwargs):
    """
    Синхронная реализация отправки сообщения через Telegram API.

    :param bot_token: Токен бота Telegram
    :param chat_id: ID чата, в который отправляется сообщение
    :param text: Текст сообщения
    :param kwargs: Дополнительные параметры, которые принимает sendMessage метод Telegram API
    :return: Ответ от Telegram API
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Параметры запроса
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        **kwargs
    }

    try:
        # Отправляем сообщение в Telegram API
        response = requests.post(url, json=payload)
        response.raise_for_status()

        # Получаем JSON-ответ
        response_data = response.json()

        user, created = User.objects.get_or_create(telegram_id=chat_id)

        # Сохраняем сообщение в базу данных
        TelegramMassage.objects.create(
            user=user,
            type=type,
            massage=text,
        )

        return response_data

    except requests.exceptions.HTTPError as http_err:
        raise Exception(f"HTTP error occurred: {http_err}")
    except Exception as err:
        raise Exception(f"An error occurred: {err}")
    

def send_message_to_staffs(text: str, type: str = TelegramMassage.MISC, partner_id: str = None, bot_token: str = DEFAULT_BOT, **kwargs):
    if type == TelegramMassage.TECHNICAL:
        staffs = Staff.objects.filter(is_active=True, notif=Staff.TECHNICAL)
    elif type == TelegramMassage.STATUS: 
        staffs = Staff.objects.filter(is_active=True, notif__in=[Staff.STATUS, Staff.TECHNICAL])
    else:
        staffs = Staff.objects.filter(is_active=True).exclude(notif=Staff.OFF)
    
    if partner_id:
        staffs = staffs.filter(
            Q(user__partners__id=partner_id) | Q(user__is_staff=True)
        )

    for staff in staffs:
        send_message(staff.telegram_id, text, type, bot_token, **kwargs)