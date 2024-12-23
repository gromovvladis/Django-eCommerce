from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
from django.conf import settings
from aiogram.client.bot import DefaultBotProperties

staff_bot = None
customer_bot = None
support_bot = None

staff_dp = None
customer_dp = None
support_dp = None

if settings.TELEGRAM_STAFF_BOT_TOKEN:
    staff_bot = Bot(token=settings.TELEGRAM_STAFF_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    if settings.DEBUG:
        staff_storage = MemoryStorage()
    else:
        staff_storage = RedisStorage.from_url('redis://127.0.0.1:6379/5')
        
    staff_dp = Dispatcher(storage=staff_storage)

if settings.TELEGRAM_CUSTOMER_BOT_TOKEN:
    customer_bot = Bot(token=settings.TELEGRAM_CUSTOMER_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    if settings.DEBUG:
         customer_storage = MemoryStorage()
    else:
        customer_storage = RedisStorage.from_url('redis://127.0.0.1:6379/6')
        
    customer_dp = Dispatcher(storage=customer_storage)

if settings.TELEGRAM_SUPPORT_BOT_TOKEN:
    support_bot = Bot(token=settings.TELEGRAM_SUPPORT_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    if settings.DEBUG:
         support_storage = MemoryStorage()
    else:
        support_storage = RedisStorage.from_url('redis://127.0.0.1:6379/7')
        
    support_dp = Dispatcher(storage=support_storage)
