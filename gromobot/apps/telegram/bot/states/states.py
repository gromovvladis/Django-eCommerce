from aiogram.filters.state import State, StatesGroup


class UserAuth(StatesGroup):
    phone_number = State()


class StaffOrders(StatesGroup):
    orders = State()


class StaffNotif(StatesGroup):
    notif_status = State()
    notif_edit = State()


class StaffSite(StatesGroup):
    open_site = State()


class StaffReport(StatesGroup):
    get_report = State()
