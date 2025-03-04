from asgiref.sync import sync_to_async
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from oscar.core.compat import get_user_model
from oscar.core.loading import get_model
from oscar.apps.telegram.bot.keyboards.default.user_register import (
    contact_request_buttons,
)
from oscar.apps.telegram.bot.states.states import UserAuth

Staff = get_model("user", "Staff")
NotificationSetting = get_model("user", "NotificationSetting")
User = get_user_model()


async def get_user_by_telegram_id(telegram_id: int):
    try:
        user = await User.objects.aget(telegram_id=telegram_id)
        return user
    except User.DoesNotExist:
        return None


async def get_staff_by_telegram_id(telegram_id: int):
    try:
        staff = await Staff.objects.aget(user__telegram_id=telegram_id)
        return staff
    except Staff.DoesNotExist:
        return None


async def get_staff_by_contact(number, user_id: int):
    if number:
        try:
            user, created = await link_telegram_to_staff(number, user_id)
            if created:
                return user, "Вы успешно подписались на уведомления."
            else:
                return user, "Вы уже подписаны на уведомления."
        except User.DoesNotExist:
            return (
                None,
                "Ваш номер телефона не найден в базе данных или вы не являетесь сотрудником. Обратитесь к администратору.",
            )
    else:
        return None, "Ошибка при получении номера телефона."


async def user_is_staff(telegram_id: int) -> bool:
    try:
        await Staff.objects.aget(user__telegram_id=telegram_id, is_active=True)
        return True
    except Staff.DoesNotExist:
        return False


async def check_staff_status(message: Message, state: FSMContext) -> bool:
    """
    Проверяет, является ли пользователь staff.
    Если нет, переводит в состояние авторизации и возвращает False.
    Если да, возвращает True.
    """
    is_staff = await user_is_staff(message.from_user.id)
    if not is_staff:
        await state.set_state(UserAuth.phone_number)
        await message.answer(
            "Пройдите авторизацию!", reply_markup=contact_request_buttons
        )
        return False
    return True


async def get_current_notif(telegram_id: int):
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        return "Пользователь не найден"

    notification_settings = await sync_to_async(
        lambda: list(
            user.notification_settings.filter(
                code__in=NotificationSetting.STAFF_NOTIF
            ).all()
        )
    )()

    if not notification_settings:
        return "Уведомления не настроены"

    return "\n".join(notif.name for notif in notification_settings)


# ================= sync ====================


@sync_to_async(thread_sensitive=True)
def change_notif(telegram_id: str, new_status: str):
    try:
        user = User.objects.get(telegram_id=telegram_id)
        notif, _ = NotificationSetting.objects.get_or_create(code=new_status)

        if user.notification_settings.filter(code=new_status).exists():
            user.notification_settings.remove(notif)
        else:
            user.notification_settings.add(notif)
        user.save()
    except Staff.DoesNotExist:
        pass


@sync_to_async(thread_sensitive=True)
def link_telegram_to_user(phone_number: str, user_id: str):
    """
    Привязывает Telegram ID к пользователю на основе номера телефона.
    """
    try:
        user = User.objects.get(username=phone_number)
        user.telegram_id = user_id
        user.save()
        return user
    except User.DoesNotExist:
        return None


@sync_to_async(thread_sensitive=True)
def link_telegram_to_staff(phone_number: str, user_id: str):
    """
    Привязывает Telegram ID к пользователю и создает/обновляет запись в Staff.
    """
    user, _ = User.objects.get_or_create(
        username=phone_number, defaults={"telegram_id": user_id}
    )
    user.is_staff = True
    user.telegram_id = user_id
    user.save()

    staff, created = Staff.objects.get_or_create(
        user=user,
        defaults={
            "is_active": user.is_active,
        },
    )

    return staff, created


@sync_to_async(thread_sensitive=True)
def get_staffs():
    return Staff.objects.filter(is_active=True)
