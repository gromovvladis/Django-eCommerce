from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from oscar.apps.telegram.bot.const_texts import report_text, staffs_text, customers_text

staff_buttons = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Выберите команду",
    keyboard=[
        [
            KeyboardButton(
                text=report_text,
            ),
            KeyboardButton(
                text=staffs_text,
            ),
            KeyboardButton(
                text=customers_text,
            )
        ]
    ]
)