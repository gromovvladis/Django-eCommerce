from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from oscar.apps.telegram.bot.const_texts import phone_text, cancel_text

contact_request_buttons = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Авторизация по номеру телефона",
    keyboard=[
        [
            KeyboardButton(
                text=phone_text,
                request_contact=True
            )
        ],
        [
            KeyboardButton(text=cancel_text)
        ]
    ]
)