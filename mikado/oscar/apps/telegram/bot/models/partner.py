from asgiref.sync import sync_to_async

from oscar.core.loading import get_model
Partner = get_model("partner", "Partner")

@sync_to_async
def get_partners(user):
    return Partner.objects.filter(users=user).prefetch_related("addresses")

@sync_to_async
def partners_list(partners):
    if not partners.exists():
        return ("Нет точек продаж, к которым в прикреплены, как сотрудник.",)
    else:
        msg_list = ["Точки продажи к которым вы приклеплены, как сотрудник:"]
        for partner in partners:
            order_msg = (
                f"<b>{partner.name}</b>\n"
                f"Адрес: {partner.primary_address}\n"
            )
            
            msg_list.append(order_msg)

        return "\n\n".join(msg_list)


async def get_partners_message(partners):
    return await partners_list(partners)

