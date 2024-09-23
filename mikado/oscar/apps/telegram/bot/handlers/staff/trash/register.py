import logging

from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

from aiogram import types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from apps.user.models import Staff
from oscar.apps.telegram.bot.const_texts import *
from oscar.apps.telegram.bot.states.states import UserRegister
from oscar.apps.telegram.bot.keyboards.default import make_buttons, contact_request_button

from bot_loader import dp

@dp.message(Command("register"))
async def register(message: types.Message):
    await UserRegister.username.set()
    await message.answer(
        text=c_input_phone_number,
        reply_markup=contact_request_button
    )


@dp.message(StateFilter(UserRegister.username))
async def register_get_or_create_user(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number
    if not phone_number.startswith("+"):
        phone_number = "+" + phone_number

    user = await get_user_model().objects.filter(username=phone_number).afirst()
    if user:
        telegram_user = await Staff.objects.aget_or_create(chat_id=message.from_user.id)
        await sync_to_async(telegram_user.set_user)(user)
        await message.answer(
            text=c_successfully_register,
            reply_markup=make_buttons([c_about_us])
        )
        logging.info(f"{user.username} user was successfully connected")
        await state.finish()
        return

    await UserRegister.next()
    await message.answer(
        text=c_input_first_name,
        reply_markup=make_buttons(
            words=[message.from_user.first_name, c_cancel]
        )
    )

    await state.update_data(username=phone_number)


@dp.message(StateFilter(UserRegister.first_name))
async def register_first_name(message: types.Message, state: FSMContext):
    await UserRegister.next()
    await message.answer(
        text=c_input_last_name,
        reply_markup=make_buttons(
            words=[message.from_user.last_name, c_cancel]
        )
    )
    await state.update_data(first_name=message.text)


@dp.message(StateFilter(UserRegister.last_name))
async def register_last_name(message: types.Message, state: FSMContext):
    await UserRegister.next()
    await message.answer(
        text=c_input_password,
        reply_markup=make_buttons(
            words=[c_cancel]
        )
    )
    await state.finish()
    logging.info("user was successfully created")

