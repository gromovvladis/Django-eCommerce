from aiogram.filters.state import StatesGroup, State

class UserAuth(StatesGroup):
    phone_number = State()
