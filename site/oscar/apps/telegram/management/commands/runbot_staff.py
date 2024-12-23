import asyncio
import logging

from django.core.management.base import BaseCommand
from bot_loader import staff_dp, staff_bot

from oscar.apps.telegram.bot.middlewares import *
from oscar.apps.telegram.bot.handlers import *
from oscar.apps.telegram.bot.utils.notify_admins import on_startup_notify
from oscar.apps.telegram.bot.utils.set_bot_commands import set_staffbot_commands

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def on_startup(bot, dp):
    await set_staffbot_commands(dp)
    await on_startup_notify(bot, "персонала")


class Command(BaseCommand):
    help = 'RUN COMMAND: python manage.py runbot_staff'

    def handle(self, *args, **options):
        try:
            asyncio.run(self.start_polling())
        except KeyboardInterrupt:
            logging.info("Staff Bot Off")

    async def start_polling(self):
        logging.info("Staff Bot Start")
        await on_startup(staff_bot, staff_dp)
        await staff_dp.start_polling(staff_bot)

