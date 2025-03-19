from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from apps.telegram.bot.const_texts import cancel_text, notif_edit_text, success_text
from apps.telegram.bot.keyboards.default.edit_status import edit_notif_buttons
from apps.telegram.bot.keyboards.default.open_site import open_site_button
from apps.telegram.bot.keyboards.default.staff_keyboard import staff_buttons
from apps.telegram.bot.keyboards.inline.notifications import get_notif_keyboard
from apps.telegram.bot.models.user import (
    change_notif,
    check_staff_status,
    get_current_notif,
)
from apps.telegram.bot.states.states import StaffNotif, StaffSite

settings_router = Router()


# ============= settings ================


@settings_router.message(Command("settings"))
async def notif(message: Message, state: FSMContext):
    if await check_staff_status(message, state):
        await state.set_state(StaffNotif.notif_status)
        telegram_id = message.from_user.id
        current_notif = await get_current_notif(telegram_id)
        await message.answer(
            f"Настройка уведомлений.\n\nТекущие настройки уведомлений:\n\n<b>{current_notif}</b>",
            reply_markup=edit_notif_buttons,
        )


@settings_router.message(StaffNotif.notif_status, F.text == notif_edit_text)
async def notif_edit(message: Message, state: FSMContext):
    await state.set_state(StaffNotif.notif_edit)
    await message.answer(
        "Настройка уведомлений",
        reply_markup=await get_notif_keyboard(message.from_user.id),
    )


@settings_router.message(StaffNotif.notif_status, F.text == cancel_text)
async def notif_edit_cancel(message: Message, state: FSMContext):
    await message.answer("Настройки не изменены", reply_markup=staff_buttons)
    await state.clear()


@settings_router.callback_query(StaffNotif.notif_edit)
async def notif_edit_success(callback: CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    data = callback.data
    if data == success_text:
        await callback.message.answer(
            "Настройки сохранены!", reply_markup=staff_buttons
        )
        await state.clear()
        await callback.answer()
        return

    await change_notif(telegram_id, data)
    new_keyboard = await get_notif_keyboard(telegram_id)
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)


# ============= open site ================


@settings_router.message(Command("site"))
async def open_site(message: Message, state: FSMContext):
    await state.set_state(StaffSite.open_site)
    await message.answer(
        "Нажмите на кнопку ниже, чтобы открыть панель управления",
        reply_markup=open_site_button,
    )


@settings_router.message(StaffSite.open_site, F.text == cancel_text)
async def handle_webapp_return(message: Message, state: FSMContext):
    await message.answer("Меню сайта закрыто", reply_markup=staff_buttons)
    await state.clear()
