
import logging
from django.conf import settings

from apps.communication.tasks import _send_push_notification
from oscar.core.loading import get_model

WebPushSubscription = get_model("communication", "WebPushSubscription")
    
logger = logging.getLogger("oscar.communications")

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
    if not settings.DEBUG: 
        _send_push_notification.delay(subscription_info, payload)
    else:
        _send_push_notification(subscription_info, payload)


def send_push_notification_to_user(user, title, body, icon=None, url=None):
    try:
        subscription = WebPushSubscription.objects.get(user=user)
        send_push_notification(subscription, title, body, icon, url)
    except:
        logger.info("Пользователь %s не подписан на уведомления" % user)

