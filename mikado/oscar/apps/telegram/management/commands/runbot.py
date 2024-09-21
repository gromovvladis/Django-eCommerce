import asyncio
import logging

from django.core.management.base import BaseCommand
from bot_loader import dp, bot

from oscar.apps.telegram.bot.middlewares import *
from oscar.apps.telegram.bot.handlers import *
from oscar.apps.telegram.bot.utils.notify_admins import on_startup_notify
from oscar.apps.telegram.bot.utils.set_bot_commands import set_default_commands

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def on_startup(bot, dp):
    logging.info("on_startup")
    await set_default_commands(dp)
    await on_startup_notify(bot)


class Command(BaseCommand):
    help = 'RUN COMMAND: python manage.py runbot'

    def handle(self, *args, **options):
        asyncio.run(self.start_polling())

    async def start_polling(self):
        logging.info("Start")
        await on_startup(bot, dp)
        await dp.start_polling(bot)
