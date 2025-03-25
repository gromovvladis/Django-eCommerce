from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from apps.telegram.bot.keyboards.inline.orders import orders_keyboard
from apps.telegram.bot.models.order import (get_orders, get_orders_message,
                                            get_period)
from apps.telegram.bot.models.user import check_staff_status
from apps.telegram.bot.states.states import StaffOrders

orders_router = Router()


# ============= orders ================


async def process_orders(callback: CallbackQuery, period: str):
    """
    Получает заказы за указанный период, формирует сообщение и очищает состояние.
    """
    start, end = await get_period(period)
    orders = await get_orders(start_period=start)
    msg_list = await get_orders_message(orders)
    await callback.answer()
    await callback.message.edit_reply_markup()
    await callback.message.edit_text(
        f"Заказы за {period} \n\n Начало периода: {start.strftime('%d.%m.%Y %H:%M')}\n Конец периода: {end.strftime('%d.%m.%Y %H:%M')}"
    )

    for i in range(0, len(msg_list), 10):
        msg = "\n\n".join(msg_list[i : i + 10])
        await callback.message.answer(msg)


@orders_router.message(Command("orders"))
async def orders(message: Message, state: FSMContext):
    if await check_staff_status(message, state):
        await state.set_state(StaffOrders.orders)
        await message.answer(
            "За какой период показать заказы?", reply_markup=orders_keyboard
        )


@orders_router.callback_query(StaffOrders.orders, F.data == "orders_today")
async def orders_today(callback: CallbackQuery, state: FSMContext):
    await process_orders(callback, "сегодня")
    await state.clear()


@orders_router.callback_query(StaffOrders.orders, F.data == "orders_week")
async def orders_yesterday(callback: CallbackQuery, state: FSMContext):
    await process_orders(callback, "неделю")
    await state.clear()


@orders_router.callback_query(StaffOrders.orders, F.data == "orders_month")
async def orders_week(callback: CallbackQuery, state: FSMContext):
    await process_orders(callback, "месяц")
    await state.clear()


# ============= active orders ================


@orders_router.message(Command("activeorders"))
async def active_orders(message: Message, state: FSMContext):
    if await check_staff_status(message, state):

        orders = await get_orders(only_active=True)
        msg_list = await get_orders_message(orders)
        if msg_list:
            await message.answer("Активные заказы")

            for i in range(0, len(msg_list), 10):
                msg = "\n\n".join(msg_list[i : i + 10])
                await message.answer(msg)
        else:
            await message.answer("Нет активных заказов")
