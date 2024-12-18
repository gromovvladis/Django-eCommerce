import logging

from aiogram import Bot

from django.conf import settings


async def on_startup_notify(bot: Bot):
    for admin in settings.TELEGRAM_ADMINS_LIST:
        try:
            await bot.send_message(admin, "Бот запущен")

        except Exception as err:
            logging.exception(err)
