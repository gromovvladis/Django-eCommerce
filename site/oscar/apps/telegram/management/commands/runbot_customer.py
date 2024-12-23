import asyncio
import logging

from django.core.management.base import BaseCommand
from bot_loader import customer_bot, customer_dp

from oscar.apps.telegram.bot.middlewares import *
from oscar.apps.telegram.bot.handlers import *
from oscar.apps.telegram.bot.utils.notify_admins import on_startup_notify
from oscar.apps.telegram.bot.utils.set_bot_commands import set_customerbot_commands

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def on_startup(bot, dp):
    await set_customerbot_commands(dp)
    await on_startup_notify(bot, "клиентский")


class Command(BaseCommand):
    help = 'RUN COMMAND: python manage.py runbot_customer'

    def handle(self, *args, **options):
        try:
            asyncio.run(self.start_polling())
        except KeyboardInterrupt:
            logging.info("Customer Bot Off")

    async def start_polling(self):
        logging.info("Customer Bot Start")
        await on_startup(customer_bot, customer_dp)
        await customer_dp.start_polling(customer_bot)

