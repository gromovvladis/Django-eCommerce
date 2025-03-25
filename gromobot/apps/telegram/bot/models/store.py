from asgiref.sync import sync_to_async
from core.loading import get_model

Store = get_model("store", "Store")


@sync_to_async
def get_stores(user):
    return Store.objects.filter(users=user).prefetch_related("address")


@sync_to_async
def stores_list(stores):
    if not stores.exists():
        return "Нет точек продаж, к которым в прикреплены, как сотрудник."
    else:
        msg_list = ["Магазины к которым вы приклеплены, как сотрудник:"]
        for store in stores:
            order_msg = f"<b>{store.name}</b>\n" f"Адрес: {store.primary_address}\n"

            msg_list.append(order_msg)

        return "\n\n".join(msg_list)


async def get_stores_message(stores):
    return await stores_list(stores)
