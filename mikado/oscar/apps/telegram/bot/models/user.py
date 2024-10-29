from asgiref.sync import sync_to_async
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from django.db.models import Q

from oscar.core.compat import get_user_model
from oscar.core.loading import get_model
from oscar.apps.telegram.bot.keyboards.default.user_register import contact_request_buttons
from oscar.apps.telegram.bot.states.states import UserAuth

Staff = get_model("user", "Staff")
User = get_user_model()

async def get_user_by_telegram_id(telegram_id: int):
    try:
        user = await User.objects.aget(telegram_id=telegram_id)
        return user
    except User.DoesNotExist:
        return None


async def get_or_create_staff_by_user_id(user_id: int):
    user, created = await Staff.objects.aget_or_create(telegram_id=user_id)
    return user


async def get_staff_by_telegram_id(telegram_id: int):
    try:
        staff = await Staff.objects.aget(telegram_id=telegram_id)
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
            return None, "Ваш номер телефона не найден в базе данных или вы не являетесь сотрудником. Обратитесь к администратору."
    else:
        return None, "Ошибка при получении номера телефона."


async def user_is_staff(telegram_id: int) -> bool:
    try:
        staff = await Staff.objects.aget(telegram_id=telegram_id, is_active=True)
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
        await message.answer('Пройдите авторизацию!', reply_markup=contact_request_buttons)
        return False
    return True


async def get_current_notif(telegram_id: int):
    staff = await get_staff_by_telegram_id(telegram_id)
    if staff:
        return next((description for key, description in Staff.NOTIF_CHOICES if key == staff.notif), "Уведомления не настроены")
    return None


# ================= sync ====================


@sync_to_async
def change_notif(telegram_id: int, new_status: str):
    try:
        staff = Staff.objects.get(telegram_id=telegram_id)
        staff.notif = new_status
        staff.save()
        return "Настройки уведомлений обновлены"
    except Staff.DoesNotExist:
        return "Настройки не примены. Телеграм не свзяан с профилем персонала"


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
    user, _ = User.objects.filter(
        Q(is_staff=True) | Q(groups__isnull=False)
    ).get_or_create(
        username=phone_number,
        defaults={'telegram_id': user_id}
    )
    user.telegram_id = user_id
    user.save()
    
    staff, created = Staff.objects.get_or_create(
        user=user,
        defaults={'is_active': user.is_active, 'telegram_id': user_id, 'notif': Staff.NEW}
    )
    staff.telegram_id = user_id
    staff.save()

    return staff, created


@sync_to_async
def get_staffs():
    return Staff.objects.filter(is_active=True)
