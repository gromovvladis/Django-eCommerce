from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from oscar.apps.telegram.bot.const_texts import start_phone_number, cancel_btn

contact_request_buttons = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Авторизация по номеру телефона",
    keyboard=[
        [
            KeyboardButton(
                text=start_phone_number,
                request_contact=True
            )
        ],
        [
            KeyboardButton(text=cancel_btn)
        ]
    ]
)