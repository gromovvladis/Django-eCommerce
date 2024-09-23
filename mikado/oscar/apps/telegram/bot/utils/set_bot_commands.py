from aiogram import Dispatcher

from oscar.apps.telegram.bot.handlers.staff.start import staff_router


async def set_default_commands(dp: Dispatcher):
    dp.include_router(staff_router)
