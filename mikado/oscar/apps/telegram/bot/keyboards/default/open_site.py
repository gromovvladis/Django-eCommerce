from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from oscar.apps.telegram.bot.const_texts import cancel_btn, open_site
from django.conf import settings


open_site_button = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Открыть сайт",
    keyboard=[
        [KeyboardButton(
            text=open_site,
            web_app=WebAppInfo(url=f"https://{settings.ALLOWED_HOSTS[0]}")
        )],
        [KeyboardButton(
            text=cancel_btn,
        )],
])