from datetime import timedelta
from django.utils import timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from oscar.apps.telegram.bot.keyboards.inline.reports import report_keyboard
from oscar.apps.telegram.bot.models.user import check_staff_status
from oscar.apps.telegram.bot.models.report import get_report_message, get_customers_message, get_staffs_message
from oscar.apps.telegram.bot.states.states import StaffReport
from oscar.apps.telegram.bot.const_texts import report_text, customers_text, staffs_text

report_router = Router()

    
# ============= reports ================


async def get_report(callback, start_period):
    msg = await get_report_message(start_period)
    await callback.answer()
    await callback.message.edit_reply_markup()
    await callback.message.edit_text(f"<b>Отчет за указанный период</b>\n\nНачало периода: {start_period.strftime('%d.%m.%Y %H:%M')}\nКонец периода: {timezone.now().strftime('%d.%m.%Y %H:%M')}\n\n"f"{msg}")


@report_router.message(F.text == report_text)
async def report(message: Message, state: FSMContext):
    if await check_staff_status(message, state):
        await state.set_state(StaffReport.get_report)
        await message.answer(f"За какой период сформировать отчет?", reply_markup=report_keyboard)


@report_router.callback_query(StaffReport.get_report, F.data == 'report_today')
async def report_today(callback: CallbackQuery, state: FSMContext):
    start_period = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    await get_report(callback, start_period)
    await state.clear()


@report_router.callback_query(StaffReport.get_report, F.data == 'report_week')
async def report_week(callback: CallbackQuery, state: FSMContext):
    start_period = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    await get_report(callback, start_period)
    await state.clear()


@report_router.callback_query(StaffReport.get_report, F.data == 'report_month')
async def report_month(callback: CallbackQuery, state: FSMContext):
    start_period = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30)
    await get_report(callback, start_period)
    await state.clear()


@report_router.message(F.text == staffs_text)
async def get_staffs(message: Message, state: FSMContext):
    if await check_staff_status(message, state):
        msg = await get_staffs_message()
        await message.answer(msg)


@report_router.message(F.text == customers_text)
async def get_customers(message: Message, state: FSMContext):
    if await check_staff_status(message, state):
        msg = await get_customers_message()
        await message.answer(msg)
