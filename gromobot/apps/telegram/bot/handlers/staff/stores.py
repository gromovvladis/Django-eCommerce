from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from apps.telegram.bot.models.store import get_stores, get_stores_message
from apps.telegram.bot.models.user import (check_staff_status,
                                           get_user_by_telegram_id)

store_router = Router()

# ============= store ================


@store_router.message(Command("stores"))
async def stores(message: Message, state: FSMContext):
    if await check_staff_status(message, state):
        telegram_id = message.from_user.id
        user = await get_user_by_telegram_id(telegram_id)
        stores = await get_stores(user)
        msg = await get_stores_message(stores)
        await message.answer(msg)
