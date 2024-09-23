from aiogram import types
from aiogram.filters import Command
from django.conf import settings

from bot_loader import dp

# Проверка, является ли пользователь администратором
async def is_admin(user_id: int) -> bool:
    # Здесь должна быть логика проверки, является ли пользователь администратором
    # Например, можно проверять список ID администраторов
    admin_ids = settings.TELEGRAM_ADMINS_LIST  # Замените на ваши ID администраторов
    return user_id in admin_ids

# Фильтр для администраторов
class AdminFilter:
    async def __call__(self, message: types.Message):
        return await is_admin(message.from_user.id)
    

@dp.message(Command("register"), AdminFilter())
async def admin_start(message: types.Message):
    await message.reply("Hello, admin!")
