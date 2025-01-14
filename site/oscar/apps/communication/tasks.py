import json
import logging
from django.conf import settings
from django.templatetags.static import static

from celery import shared_task
from pywebpush import webpush, WebPushException

from django.template import loader
from django.contrib.auth import get_user_model

from oscar.apps.order.client import EvotorKomtet
from oscar.apps.telegram.bot.synchron.send_message import send_message_to_staffs, send_message
from oscar.core.loading import get_model


Notification = get_model("communication", "Notification")
WebPushSubscription = get_model("user", "WebPushSubscription")
TelegramMessage = get_model("telegram", "TelegramMessage")
User = get_user_model()

logger = logging.getLogger("oscar.communications")

# ================= Site Notification =================

@shared_task
def _notify_staff_about_new_order(ctx: dict):

    subject = "Пользовательский заказ"
    message_tpl = loader.get_template("oscar/customer/alerts/staff_new_order_message.html")
    description = "Заказ №%s успешно создан!" % (ctx['number'])
    staffs = User.objects.filter(is_staff=True)

    for staff in staffs:
        Notification.objects.create(
            recipient=staff, 
            order_id=ctx["order_id"],
            subject=subject, 
            body=message_tpl.render(ctx).strip(), 
            description=description,
            status="Success"
        )

@shared_task()
def _notify_customer_about_new_order(ctx: dict):
    
    subject = "Новый заказ"
    message_tpl = loader.get_template("oscar/customer/alerts/new_order_message.html")
    description = "Заказ №%s успешно создан!" % (ctx['number'])

    ctx['description'] = description

    Notification.objects.create(
        recipient_id=ctx['user_id'],
        order_id=ctx["order_id"],
        subject=subject,
        body=message_tpl.render(ctx).strip(), 
        description=description,
        status="Success"
    )

@shared_task()
def _notify_customer_about_order_status(ctx: dict):
    
    subject = "Статус заказа изменен"
    message_tpl = loader.get_template("oscar/customer/alerts/order_status_chenged_message.html")
    description = "Новый статус заказа №%s - %s" % (ctx['number'], ctx['new_status'])

    status="Info"

    if ctx['new_status'] == "Отменен":
        status="Canceled"

    if ctx['new_status'] == "Обрабатывается" or ctx['new_status'] == "Ожидает оплаты":
        status="Warning"

    context = {
        'title': "Посмотреть заказ №%s" % ctx['number'],
        'url': ctx['url'],
        'new_status': ctx['new_status'],
    }

    Notification.objects.create(
        recipient_id=ctx['user_id'],
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
        logger.error(f"Ошибка отправки уведомления: {str(ex)}")

@shared_task
def _send_push_notification_new_order_to_staff(ctx):
    payload = {
        "title": "Новый заказ!",
        "body": ctx.get("order"),
        "icon": static('svg/webpush/new_order.svg'),
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
def _send_telegram_message_to_staffs(msg: str, type: str = TelegramMessage.MISC, store_id: str = None):
    send_message_to_staffs(msg, type, store_id)

@shared_task
def _send_telegram_message_to_user(telegram_id: int, msg: str, type: str):
    send_message(telegram_id, msg, type)

# ================= Evotor =================

def _send_order_to_evotor(order_json: dict):
    pass
    # EvotorKomtet().send_order(order_json)