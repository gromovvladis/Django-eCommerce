from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from apps.telegram.bot.const_texts import cancel_text, phone_text

contact_request_buttons = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Авторизация по номеру телефона",
    keyboard=[
        [KeyboardButton(text=phone_text, request_contact=True)],
        [KeyboardButton(text=cancel_text)],
    ],
)
