from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

report_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Отчет за сегодня', callback_data='report_today')],
    [InlineKeyboardButton(text='Отчет за неделю', callback_data='report_week')],
    [InlineKeyboardButton(text='Отчет за месяц', callback_data='report_month')]])