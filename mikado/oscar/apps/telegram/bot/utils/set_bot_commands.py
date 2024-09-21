from aiogram import types, Dispatcher
from oscar.apps.telegram.bot.handlers.users.echo import *
from oscar.apps.telegram.bot.handlers.users.start import *
from oscar.apps.telegram.bot.handlers.users.admin import *
from oscar.apps.telegram.bot.handlers.users.help import *
from oscar.apps.telegram.bot.handlers.users.register import *

async def set_default_commands(dp: Dispatcher):
    dp.message.register(bot_echo)
    dp.message.register(bot_echo_all)

    dp.message.register(admin_start)
    dp.message.register(start)

    dp.message.register(help)
    
    dp.message.register(register)
    dp.message.register(register_get_or_create_user)
    dp.message.register(register_first_name)
    dp.message.register(register_last_name)

