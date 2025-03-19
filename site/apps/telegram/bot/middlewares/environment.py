from aiogram import BaseMiddleware
from aiogram.types import Message


class EnvironmentMiddleware(BaseMiddleware):
    skip_patterns = ["error", "update"]

    def __init__(self, **kwargs):
        super().__init__()
        self.kwargs = kwargs

    async def on_pre_process_message(self, message: Message, data: dict, *args):
        data.update(**self.kwargs)
