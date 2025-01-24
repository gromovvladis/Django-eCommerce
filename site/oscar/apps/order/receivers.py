from django.conf import settings
from datetime import timedelta

from django.dispatch import receiver
from django.utils.timezone import now

from oscar.apps.order.tasks import paying_status
from oscar.apps.order.signals import order_placed


# pylint: disable=unused-argument
@receiver(order_placed)
def receive_order_placed(sender, order, user, **kwargs):
    if order.status == settings.OSCAR_INITIAL_ONLINE_PAYMENT_ORDER_STATUS and not settings.DEBUG:
        paying_status.apply_async(args=[order.number], eta=now() + timedelta(minutes=11))
