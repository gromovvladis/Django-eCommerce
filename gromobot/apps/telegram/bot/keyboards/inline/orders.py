from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

orders_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Заказы за сегодня", callback_data="orders_today")],
        [InlineKeyboardButton(text="Заказы за неделю", callback_data="orders_week")],
        [InlineKeyboardButton(text="Заказы за месяц", callback_data="orders_month")],
    ]
)
