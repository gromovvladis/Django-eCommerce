from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command

from oscar.apps.telegram.bot.models import check_staff_status
from oscar.apps.telegram.bot.models.partner import get_partners, get_partners_message
from oscar.apps.telegram.bot.models.user import get_user_by_telegram_id

partner_router = Router()

# ============= partner ================


@partner_router.message(Command('partner'))
async def partners(message: Message, state: FSMContext):
    if await check_staff_status(message, state):
        telegram_id = message.from_user.id
        user = await get_user_by_telegram_id(telegram_id)
        partners = await get_partners(user)
        msg = await get_partners_message(partners)
        await message.answer(msg)