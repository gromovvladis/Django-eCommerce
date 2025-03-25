import asyncio
import logging

# from apps.telegram.bot.middlewares import *
# from apps.telegram.bot.handlers import *
from apps.telegram.bot.utils.notify_admins import on_startup_notify
from apps.telegram.bot.utils.set_bot_commands import set_staffbot_commands
from bot_loader import staff_bot, staff_dp
from django.core.management.base import BaseCommand

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def on_startup(bot, dp):
    await set_staffbot_commands(dp)
    await on_startup_notify(bot, "персонала")


class Command(BaseCommand):
    help = "RUN COMMAND: python manage.py runbot_staff"

    def handle(self, *args, **options):
        try:
            asyncio.run(self.start_polling())
        except KeyboardInterrupt:
            logging.info("Staff Bot Off")

    async def start_polling(self):
        if staff_bot:
            logging.info("Staff Bot Start")
            await on_startup(staff_bot, staff_dp)
            await staff_dp.start_polling(staff_bot)
