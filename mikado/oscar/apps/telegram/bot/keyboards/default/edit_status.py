from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from oscar.apps.telegram.bot.const_texts import notif_edit, cancel_btn

edit_notif_buttons = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Изменить настройки уведомлений?",
    keyboard=[
        [
            KeyboardButton(
                text=notif_edit,
            )
        ],
        [
            KeyboardButton(text=cancel_btn)
        ]
    ]
)