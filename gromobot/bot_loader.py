from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from django.conf import settings

staff_bot = None
customer_bot = None
support_bot = None

staff_dp = None
customer_dp = None
support_dp = None

if settings.TELEGRAM_STAFF_BOT_TOKEN:
    staff_bot = Bot(
        token=settings.TELEGRAM_STAFF_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    if settings.CELERY:
        staff_storage = RedisStorage.from_url(settings.TELEGRAM_STAFF_BROKER_URL)
    else:
        staff_storage = MemoryStorage()

    staff_dp = Dispatcher(storage=staff_storage)

if settings.TELEGRAM_CUSTOMER_BOT_TOKEN:
    customer_bot = Bot(
        token=settings.TELEGRAM_CUSTOMER_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    if settings.CELERY:
        customer_storage = RedisStorage.from_url(settings.TELEGRAM_CUSTOMER_BROKER_URL)
    else:
        customer_storage = MemoryStorage()

    customer_dp = Dispatcher(storage=customer_storage)

if settings.TELEGRAM_SUPPORT_BOT_TOKEN:
    support_bot = Bot(
        token=settings.TELEGRAM_SUPPORT_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    if settings.CELERY:
        support_storage = RedisStorage.from_url(settings.TELEGRAM_SUPPORT_BROKER_URL)
    else:
        support_storage = MemoryStorage()

    support_dp = Dispatcher(storage=support_storage)
