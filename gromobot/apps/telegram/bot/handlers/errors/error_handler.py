import logging

from aiogram.exceptions import (TelegramAPIError, TelegramRetryAfter,
                                TelegramUnauthorizedError)
from bot_loader import dp


@dp.errors_handler()
async def errors(update, exception):
    """
    Exceptions handler. Catches all exceptions within task factory tasks.
    :param dispatcher:
    :param update:
    :param exception:
    :return: stdout logging
    """

    if isinstance(exception, TelegramUnauthorizedError):
        logging.exception(f"Unauthorized: {exception}")
        return True

    if isinstance(exception, TelegramAPIError):
        logging.exception(f"TelegramAPIError: {exception} \nUpdate: {update}")
        return True

    if isinstance(exception, TelegramRetryAfter):
        logging.exception(f"RetryAfter: {exception} \nUpdate: {update}")
        return True

    logging.exception(f"Update: {update} \n{exception}")
