from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from django.conf import settings
from aiogram.client.bot import DefaultBotProperties

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
if settings.DEBUG:
    storage = MemoryStorage()
else:
    storage = RedisStorage.from_url('redis://127.0.0.1:6379/5', key_builder=DefaultKeyBuilder(with_prefix='bot_fsm')  )
dp = Dispatcher(storage=storage)
