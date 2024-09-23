import os, django
from decouple import config

os.environ.setdefault("DJANGO_SETTINGS_MODULE", config("DJANGO_SETTINGS_MODULE"))
django.setup()

import logging
logger = logging.getLogger(__name__)

from asgiref.sync import sync_to_async

from django.db.models import Q
from oscar.core.compat import get_user_model
from oscar.core.loading import get_model
Staff = get_model("user", "Staff")
User = get_user_model()


async def get_or_create_user_by_id(user_id: int):
    user, created = Staff.objects.aget_or_create(telegram_id=user_id)
    if created:
        logger.info(f"user {user_id} was added to DB")
    else:
        logger.info(f"User {user_id} is already exist")
    return user


async def get_user_by_id(user_id: int):
    try:
        staff = Staff.objects.aget(telegram_id=user_id)
        return staff
    except Staff.DoesNotExist:
        return None


async def get_user_by_contact(number, user_id: int):
    if number:
        try:
            user, created = await link_telegram_to_staff(number, user_id)
            if created:
                return user, "Вы успешно подписались на уведомления."
            else:
                return user, "Вы уже подписаны на уведомления."
        except User.DoesNotExist:
            return None, "Ваш номер телефона не найден в базе данных или вы не являетесь сотрудником. Обратитесь к администратору."
    else:
        return None, "Ошибка при получении номера телефона."


@sync_to_async
def link_telegram_to_user(phone_number: str, user_id: str):
    """
    Привязывает Telegram ID к пользователю на основе номера телефона.
    """
    try:
        user = User.objects.filter(
            Q(is_staff=True) | Q(groups__isnull=False)
        ).get(username=phone_number)
        user.telegram_id = user_id
        user.save()
        return user
    except User.DoesNotExist:
        return None


@sync_to_async
def link_telegram_to_staff(phone_number: str, user_id: str):
    """
    Привязывает Telegram ID к пользователю и создает/обновляет запись в Staff.
    """
    # Ищем пользователя с правами staff или группами
    user = User.objects.filter(
        Q(is_staff=True) | Q(groups__isnull=False)
    ).get(username=phone_number)
    user.telegram_id = user_id
    user.save()
    
    staff, created = Staff.objects.get_or_create(
        user=user,
        defaults={'is_active': user.is_active, 'telegram_id': user_id, 'notif': Staff.NEW}
    )

    # Если запись не была создана, обновляем необходимые поля
    if not created:
        staff.telegram_id = user_id
        staff.save()

    return staff, created


@sync_to_async
def get_staffs():
    return Staff.objects.filter(is_active=True)
