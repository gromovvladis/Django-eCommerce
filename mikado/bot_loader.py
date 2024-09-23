from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
from django.conf import settings
from aiogram.client.bot import DefaultBotProperties

import logging

logging.basicConfig(
    format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
    level=logging.INFO,
)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
if settings.DEBUG:
    storage = MemoryStorage()
else:
    storage = RedisStorage('redis://@127.0.0.1/', '6379', db=5, pool_size=10, prefix='bot_fsm') 
dp = Dispatcher(storage=storage)
