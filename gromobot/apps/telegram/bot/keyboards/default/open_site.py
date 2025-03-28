from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from apps.telegram.bot.const_texts import cancel_text, open_site_text
from django.conf import settings

open_site_button = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Панель управления",
    keyboard=[
        [
            KeyboardButton(
                text=open_site_text,
                web_app=WebAppInfo(
                    url=f"https://{settings.ALLOWED_HOSTS[0]}/dashboard"
                ),
            )
        ],
        [
            KeyboardButton(
                text=cancel_text,
            )
        ],
    ],
)
