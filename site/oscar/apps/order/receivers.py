from django.conf import settings
from datetime import timedelta

from django.dispatch import receiver
from django.utils.timezone import now

from oscar.apps.order.tasks import update_paying_status_task
from oscar.apps.order.signals import order_placed


# pylint: disable=unused-argument
@receiver(order_placed)
def update_paying_status(sender, order, user, **kwargs):
    if (
        order.status == settings.OSCAR_INITIAL_ONLINE_PAYMENT_ORDER_STATUS
        and settings.CELERY
    ):
        update_paying_status_task.apply_async(
            args=[order.number], eta=now() + timedelta(minutes=11)
        )
