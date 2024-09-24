from aiogram.filters.state import StatesGroup, State

class UserAuth(StatesGroup):
    phone_number = State()

class StaffOrders(StatesGroup):
    orders = State()

class StaffNotif(StatesGroup):
    notif_status = State()
    status_edit = State()

class OpenSite(StatesGroup):
    open_site = State()