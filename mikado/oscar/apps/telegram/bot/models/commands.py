# Не оптимизировать импорты и не менять их порядок
import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj_ac.settings")
django.setup()

import logging

from asgiref.sync import sync_to_async

from oscar.apps.telegram.models import TelegramUser

logger = logging.getLogger(__name__)


def get_or_create_user(user_id: int) -> TelegramUser:
    user, created = TelegramUser.objects.aget_or_create(telegram_id=user_id)
    if created:
        logger.info(f"user {user_id} was added to DB")
    else:
        logger.info(f"User {user_id} is already exist")
    return user


# @sync_to_async
# def get_user(user_id: int) -> TelegramUser:
#     return TelegramUser.objects.get(telegram_id=user_id)


def get_user(user_id: int) -> TelegramUser:
    return TelegramUser.objects.aget(telegram_id=user_id)
