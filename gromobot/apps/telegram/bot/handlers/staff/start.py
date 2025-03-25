from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from apps.telegram.bot.const_texts import cancel_text
from apps.telegram.bot.keyboards.default.staff_keyboard import staff_buttons
from apps.telegram.bot.keyboards.default.user_register import \
    contact_request_buttons
from apps.telegram.bot.models.user import get_staff_by_contact
from apps.telegram.bot.states.states import UserAuth

start_router = Router()


@start_router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.set_state(UserAuth.phone_number)
    await message.answer(
        "Отправьте ваш номер телефона для авторизации в системе",
        reply_markup=contact_request_buttons,
    )


@start_router.message(UserAuth.phone_number, F.contact)
async def register_number(message: Message, state: FSMContext):
    staff, msg = await get_staff_by_contact(
        message.contact.phone_number, message.from_user.id
    )
    if staff:
        if staff.has_permission:
            await message.answer(msg, reply_markup=staff_buttons)
        else:
            await message.answer(
                "Ваша учетная запись не имеет доступа или заблокирована. Пожалуйста, свяжитесь с администратором.",
                reply_markup=ReplyKeyboardRemove(),
            )
    else:
        await message.answer(msg, reply_markup=ReplyKeyboardRemove())
    await state.clear()


@start_router.message(UserAuth.phone_number, F.text == cancel_text)
async def register_number_cancel(message: Message, state: FSMContext):
    await message.edit_reply_markup(reply_markup=None)
    await state.clear()
