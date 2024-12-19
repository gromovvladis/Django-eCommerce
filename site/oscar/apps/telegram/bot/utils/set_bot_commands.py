from aiogram import Dispatcher

from oscar.apps.telegram.bot.handlers.staff.start import start_router
from oscar.apps.telegram.bot.handlers.staff.orders import orders_router
from oscar.apps.telegram.bot.handlers.staff.history import history_router
from oscar.apps.telegram.bot.handlers.staff.settings import settings_router
from oscar.apps.telegram.bot.handlers.staff.stores import store_router
from oscar.apps.telegram.bot.handlers.staff.reports import report_router


async def set_default_commands(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(orders_router)
    dp.include_router(history_router)
    dp.include_router(settings_router)
    dp.include_router(store_router)
    dp.include_router(report_router)
