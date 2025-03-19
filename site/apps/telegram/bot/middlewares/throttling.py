from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import Message


class ThrottlingMiddleware(BaseMiddleware):
    """
    Simple middleware
    """

    def __init__(self, limit: float):
        super().__init__()
        self.limit = limit

    async def on_pre_process_message(self, message: Message, data: dict):
        try:
            # Пример работы с ограничением запросов
            pass
        except TelegramRetryAfter as exc:
            await message.answer(
                f"Пожалуйста, подождите {exc.retry_after} секунд перед следующим запросом."
            )

    async def message_throttled(self, message: Message, throttled: TelegramRetryAfter):
        if throttled.exceeded_count <= 2:
            await message.reply("Too many requests!")
