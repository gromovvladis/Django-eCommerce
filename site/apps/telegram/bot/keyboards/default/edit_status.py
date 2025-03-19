from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from apps.telegram.bot.const_texts import cancel_text, notif_edit_text

edit_notif_buttons = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Изменить настройки уведомлений?",
    keyboard=[
        [
            KeyboardButton(
                text=notif_edit_text,
            )
        ],
        [KeyboardButton(text=cancel_text)],
    ],
)
