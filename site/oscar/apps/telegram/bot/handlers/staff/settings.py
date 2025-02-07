from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from oscar.apps.telegram.bot.keyboards.default.edit_status import edit_notif_buttons
from oscar.apps.telegram.bot.keyboards.inline.notifications import notif_keyboard
from oscar.apps.telegram.bot.keyboards.default.open_site import open_site_button
from oscar.apps.telegram.bot.keyboards.default.staff_keyboard import staff_buttons
from oscar.apps.telegram.bot.const_texts import notif_edit_text, cancel_text
from oscar.apps.telegram.bot.states.states import StaffNotif, StaffSite
from oscar.apps.telegram.bot.models.user import (
    change_notif,
    check_staff_status,
    get_current_notif,
)

settings_router = Router()


# ============= settings ================


@settings_router.message(Command("settings"))
async def notif(message: Message, state: FSMContext):
    if await check_staff_status(message, state):
        await state.set_state(StaffNotif.notif_status)
        telegram_id = message.from_user.id
        current_notif = await get_current_notif(telegram_id)
        await message.answer(
            f"Настройка уведомлений.\n\nТекущий статус уведомлений: <b>{current_notif}</b>",
            reply_markup=edit_notif_buttons,
        )


@settings_router.message(StaffNotif.notif_status, F.text == notif_edit_text)
async def notif_edit(message: Message, state: FSMContext):
    await state.set_state(StaffNotif.status_edit)
    await message.answer(
        "Выберите новую настройку уведомлений", reply_markup=notif_keyboard
    )


@settings_router.message(StaffNotif.status_edit, F.text == cancel_text)
async def notif_cancel(message: Message, state: FSMContext):
    await message.answer("Настройки не изменены", reply_markup=staff_buttons)
    await state.clear()


@settings_router.message(StaffNotif.notif_status, F.text == cancel_text)
async def notif_cancel2(message: Message, state: FSMContext):
    await message.answer("Настройки не изменены", reply_markup=staff_buttons)
    await state.clear()


@settings_router.callback_query(StaffNotif.status_edit, F.data == "new-order")
async def notif_new(callback: CallbackQuery, state: FSMContext):
    msg = await change_notif(str(callback.from_user.id), "new-order")
    await callback.answer()
    await callback.message.edit_reply_markup()
    await callback.message.answer(msg, reply_markup=staff_buttons)
    await state.clear()


@settings_router.callback_query(StaffNotif.status_edit, F.data == "status-order")
async def notif_status(callback: CallbackQuery, state: FSMContext):
    msg = await change_notif(str(callback.from_user.id), "status-order")
    await callback.answer()
    await callback.message.edit_reply_markup()
    await callback.message.answer(msg, reply_markup=staff_buttons)
    await state.clear()


@settings_router.callback_query(StaffNotif.status_edit, F.data == "technical")
async def notif_technical(callback: CallbackQuery, state: FSMContext):
    msg = await change_notif(str(callback.from_user.id), "technical")
    await callback.answer()
    await callback.message.edit_reply_markup()
    await callback.message.answer(msg, reply_markup=staff_buttons)
    await state.clear()


@settings_router.callback_query(StaffNotif.status_edit, F.data == "off")
async def notif_off(callback: CallbackQuery, state: FSMContext):
    msg = await change_notif(str(callback.from_user.id), "off")
    await callback.answer()
    await callback.message.edit_reply_markup()
    await callback.message.answer(msg, reply_markup=staff_buttons)
    await state.clear()


# ============= open site ================


@settings_router.message(Command("site"))
async def open_site(message: Message, state: FSMContext):
    await state.set_state(StaffSite.open_site)
    await message.answer(
        "Нажмите на кнопку ниже, чтобы открыть сайт", reply_markup=open_site_button
    )


@settings_router.message(StaffSite.open_site, F.text == cancel_text)
async def handle_webapp_return(message: Message, state: FSMContext):
    await message.answer("Меню сайта закрыто", reply_markup=staff_buttons)
    await state.clear()
