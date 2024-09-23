from aiogram.types import Message
from aiogram.filters import Command

from bot_loader import dp

@dp.message(Command("help"))
async def bot_help(message: Message):
    text = ("Buyruqlar: ",
            "/start - Botni ishga tushirish",
            "/help - Yordam")

    await message.answer("\n".join(text))
