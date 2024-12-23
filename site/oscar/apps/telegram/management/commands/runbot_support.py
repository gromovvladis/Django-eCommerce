import asyncio
import logging

from django.core.management.base import BaseCommand
from bot_loader import support_bot, support_dp

from oscar.apps.telegram.bot.middlewares import *
from oscar.apps.telegram.bot.handlers import *
from oscar.apps.telegram.bot.utils.notify_admins import on_startup_notify
from oscar.apps.telegram.bot.utils.set_bot_commands import set_supportbot_commands

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def on_startup(bot, dp):
    await set_supportbot_commands(dp)
    await on_startup_notify(bot, "поддержки")


class Command(BaseCommand):
    help = 'RUN COMMAND: python manage.py runbot_support'

    def handle(self, *args, **options):
        try:
            asyncio.run(self.start_polling())
        except KeyboardInterrupt:
            logging.info("Support Bot Off")

    async def start_polling(self):
        logging.info("Support Bot Start")
        await on_startup(support_bot, support_dp)
        await support_dp.start_polling(support_bot)

