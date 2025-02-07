from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

from django.conf import settings

from oscar.apps.telegram.bot.const_texts import cancel_text, open_site_text


open_site_button = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Открыть сайт",
    keyboard=[
        [
            KeyboardButton(
                text=open_site_text,
                web_app=WebAppInfo(url=f"https://{settings.ALLOWED_HOSTS[0]}"),
            )
        ],
        [
            KeyboardButton(
                text=cancel_text,
            )
        ],
    ],
)
