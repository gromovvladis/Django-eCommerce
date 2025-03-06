from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command

from oscar.apps.telegram.bot.models import check_staff_status
from oscar.apps.telegram.bot.models.message import (
    get_messages,
    get_telegram_messages_message,
)
from oscar.apps.telegram.bot.models.user import get_user_by_telegram_id

history_router = Router()


@history_router.message(Command("history"))
async def orders(message: Message, state: FSMContext):
    if await check_staff_status(message, state):
        telegram_id = message.from_user.id
        user_id = await get_user_by_telegram_id(telegram_id)
        masseges = await get_messages(user_id)
        msg_list = await get_telegram_messages_message(masseges)

        await message.answer(
            "История уведомлений. Показываются последние 30 уведомлений"
        )
        limited_msg_list = msg_list[:30]

        for i in range(0, len(limited_msg_list), 10):
            msg = "\n\n".join(limited_msg_list[i : i + 10])

            # Проверяем длину сообщения
            while len(msg) > 4096:
                # Если сообщение слишком длинное, разбиваем его на части
                await message.answer(msg[:4096])  # Отправляем первые 4096 символов
                msg = msg[4096:]  # Убираем отправленную часть
            # Отправляем оставшуюся часть, если она есть
            if msg:
                await message.answer(msg)
