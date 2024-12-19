from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

notif_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Только уведомления о новых заказах', callback_data='new-order')],
    [InlineKeyboardButton(text='Уведомления об изменении заказов и новых заказах', callback_data='status-order')],
    [InlineKeyboardButton(text='Технические уведомления (Администратор)', callback_data='technical')],
    [InlineKeyboardButton(text='Отключить уведомления', callback_data='off')]
])