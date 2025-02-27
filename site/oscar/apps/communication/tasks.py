import json
import logging

from celery import shared_task
from pywebpush import webpush, WebPushException

from django.conf import settings
from django.template import loader
from django.templatetags.static import static
from django.contrib.auth import get_user_model

from oscar.core.loading import get_model
from oscar.apps.sms_auth.providers.base import Smsaero
from oscar.apps.telegram.bot.synchron.send_message import (
    send_message_to_staffs,
    send_message,
)

Notification = get_model("communication", "Notification")
CommunicationEvent = get_model("order", "CommunicationEvent")
CommunicationEventType = get_model("communication", "CommunicationEventType")
WebPushSubscription = get_model("communication", "WebPushSubscription")
TelegramMessage = get_model("telegram", "TelegramMessage")
User = get_user_model()

logger = logging.getLogger("oscar.communications")

# ================= Site Notification =================


@shared_task
def _send_site_notification_new_order_to_staff(ctx: dict):
    subject = "Пользовательский заказ"
    message_tpl = loader.get_template(
        "oscar/customer/alerts/staff_new_order_message.html"
    )
    description = "Заказ №%s успешно создан!" % (ctx["number"])
    staffs = User.objects.filter(is_staff=True)

    for staff in staffs:
        Notification.objects.create(
            recipient=staff,
            order_id=ctx["order_id"],
            subject=subject,
            body=message_tpl.render(ctx).strip(),
            description=description,
            status="Success",
        )


@shared_task()
def _send_site_notification_new_order_to_customer(ctx: dict):
    subject = "Новый заказ"
    message_tpl = loader.get_template("oscar/customer/alerts/new_order_message.html")
    description = "Заказ №%s успешно создан!" % (ctx["number"])

    ctx["description"] = description

    Notification.objects.create(
        recipient_id=ctx["user_id"],
        order_id=ctx["order_id"],
        subject=subject,
        body=message_tpl.render(ctx).strip(),
        description=description,
        status="Success",
    )


@shared_task()
def _send_sms_notification_order_status_to_customer(ctx: dict):
    event_type_name_map = {
        "Отменён": "Заказ отменён",
        "Готов": "Заказ ожидает получения",
        "Доставляется": "Заказ доставляется",
    }

    if ctx["new_status"] in event_type_name_map:
        event_name = event_type_name_map[ctx["new_status"]]
        event_type, _ = CommunicationEventType.objects.get_or_create(
            name=event_name, category="Order"
        )
        CommunicationEvent.objects.create(
            order_id=ctx["order_id"], event_type=event_type
        )

        message = None
        if ctx["new_status"] == "Отменён":
            message = f"Заказ №{ctx['number']} отменён."
        elif ctx["new_status"] == "Доставляется":
            message = f"Заказ №{ctx['number']} уже в пути!"
        elif ctx["shipping_method"] == "Самовывоз" and ctx["new_status"] == "Готов":
            message = f"Заказ №{ctx['number']} ожидает получения."

        if message:
            for admin in settings.TELEGRAM_ADMINS_LIST:
                send_message(int(admin), message)

            # auth_service = Smsaero(ctx['phone'], message)
            # auth_service.send_sms()


@shared_task()
def _send_site_notification_order_status_to_customer(ctx: dict):
    subject = "Статус заказа изменен"
    message_tpl = loader.get_template(
        "oscar/customer/alerts/order_status_chenged_message.html"
    )
    description = "Новый статус заказа №%s - %s" % (ctx["number"], ctx["new_status"])

    status = "Info"

    if ctx["new_status"] == "Отменён":
        status = "Canceled"

    if ctx["new_status"] == "Обрабатывается" or ctx["new_status"] == "Ожидает оплаты":
        status = "Warning"

    context = {
        "title": "Посмотреть заказ №%s" % ctx["number"],
        "url": ctx["url"],
        "new_status": ctx["new_status"],
    }

    Notification.objects.create(
        recipient_id=ctx["user_id"],
        order_id=ctx["order_id"],
        subject=subject,
        body=message_tpl.render(context).strip(),
        description=description,
        status=status,
    )


# ================= WEb Push Notification =================


@shared_task
def _send_push_notification(subscription_info, payload):
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=settings.WEBPUSH_PRIVATE_KEY,
            vapid_claims={
                "sub": f"mailto:{settings.WEBPUSH_ADMIN_EMAIL}",
            },
        )
    except WebPushException as ex:
        if "Push failed: 410 Gone" in str(ex):
            # Удаляем подписку из базы данных, если она больше не активна
            subscription = WebPushSubscription.objects.filter(
                endpoint=subscription_info["endpoint"]
            ).first()
            if subscription:
                subscription.delete()
                logger.info(
                    f"Подписка с endpoint {subscription_info['endpoint']} была удалена из-за ошибки 410 Gone."
                )
            else:
                logger.error(
                    f"Ошибка отправки уведомления и поиска подписки: {str(ex)}"
                )
        else:
            logger.error(f"Ошибка отправки уведомления: {str(ex)}")


@shared_task
def _send_push_notification_new_order_to_staff(ctx):
    payload = {
        "title": "Новый заказ!",
        "body": ctx.get("order"),
        "icon": static("svg/webpush/new_order.svg"),
        "url": ctx.get("staff_url"),
    }

    subscriptions = WebPushSubscription.objects.filter(user__is_staff=True)
    for subscription in subscriptions:
        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh,
                "auth": subscription.auth,
            },
        }
        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=settings.WEBPUSH_PRIVATE_KEY,
                vapid_claims={
                    "sub": f"mailto:{settings.WEBPUSH_ADMIN_EMAIL}",
                },
            )
        except WebPushException as ex:
            if "Push failed: 410 Gone" in str(ex):
                # Удаляем подписку из базы данных, если она больше не активна
                subscription.delete()
                logger.info(
                    f"Подписка с endpoint {subscription.endpoint} была удалена из-за ошибки 410 Gone."
                )
            else:
                logger.error(f"Ошибка отправки уведомления: {str(ex)}")


# ================= Telegram =================


@shared_task
def _send_telegram_message_new_order_to_staff(ctx: dict):
    msg = (
        f"<b><a href='{ctx['staff_url']}'>Новый заказ №{ctx['number']}</a></b>\n\n"
        f"{ctx['order']}\n\n"
        f"Время заказа: {ctx['order_time']}\n"
        f"Пользователь: {ctx['user']}\n"
        f"Оплата: {ctx['source']}\n"
        f"Доставка: {ctx['shipping_method']}\n"
        f"Сумма: {ctx['total']} ₽\n\n"
    )
    send_message_to_staffs(msg, TelegramMessage.NEW)


@shared_task
def _send_telegram_message_to_staffs(
    msg: str, type: str = TelegramMessage.MISC, store_id: str = None
):
    send_message_to_staffs(msg, type, store_id)


@shared_task
def _send_telegram_message_to_user(telegram_id: int, msg: str, type: str):
    send_message(telegram_id, msg, type)


# ================= Evotor =================
@shared_task
def _send_order_to_evotor(order_json: dict):
    pass
