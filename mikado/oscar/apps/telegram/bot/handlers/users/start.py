from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command

from oscar.apps.telegram.bot.keyboards.default.user_register import make_buttons
from oscar.apps.telegram.bot.models.commands import get_user

from oscar.apps.telegram.bot.const_texts import c_get_hello, c_get_hello_back, c_register, c_about_us

from bot_loader import dp

@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    data = await state.get_data()

    user = await get_user(user_id=int(message.from_user.id))
    await message.answer(f'Привет. Вы в базе с id {user.telegram_id}')

    await message.answer(f"вы ввели команду, {data.get('last_command')}")


    user = await get_user(user_id=int(message.from_user.id))
    if user is not None:
        await message.answer(
            text=c_get_hello_back(
                user.first_name,
                user.last_name),
            reply_markup=make_buttons([c_about_us])
        )
    else:
        await message.answer(
            text=c_get_hello(message.from_user.full_name),
            reply_markup=make_buttons([c_register])
        )
