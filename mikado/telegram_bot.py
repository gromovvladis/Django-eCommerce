import os
import django
from decouple import config

os.environ.setdefault("DJANGO_SETTINGS_MODULE", config("DJANGO_SETTINGS_MODULE"))
django.setup()

from telegram.ext import ApplicationBuilder
from oscar.apps.telegram.commands import link_comands
from django.conf import settings

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Основная функция для запуска бота
if __name__ == "__main__":
    link_comands(application)
    application.run_polling()
