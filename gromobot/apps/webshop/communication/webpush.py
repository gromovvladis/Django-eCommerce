import logging

from django.conf import settings
from webpush.models import PushInformation

from .tasks import _send_push_notification

logger = logging.getLogger("apps.webshop.communications")


def send_push_notification(subscription, title, body, icon=None, url=None):
    payload = {
        "title": title,
        "body": body,
        "icon": icon,
        "url": url,
    }
    subscription_info = {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh,
            "auth": subscription.auth,
        },
    }
    if settings.CELERY:
        _send_push_notification.delay(subscription_info, payload)
    else:
        _send_push_notification(subscription_info, payload)


def send_push_notification_to_user(user, title, body, icon=None, url=None):
    try:
        subscription = (
            PushInformation.objects.select_related("subscription")
            .get(user=user)
            .subscription
        )
        send_push_notification(subscription, title, body, icon, url)
    except Exception:
        logger.info("Пользователь %s не подписан на уведомления" % user)
