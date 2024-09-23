from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from oscar.apps.telegram.bot.const_texts import staff_orders_today, staff_orders_week, staff_orders_month, staff_list

staff_buttons = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Выберите команду",
    keyboard=[
        [
            KeyboardButton(
                text=staff_orders_today,
            ),
            KeyboardButton(
                text=staff_orders_week,
            ),
            KeyboardButton(
                text=staff_orders_month,
            )
        ],
        [
            KeyboardButton(text=staff_list)
        ]
    ]
)