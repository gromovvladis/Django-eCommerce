from django.dispatch import receiver

from oscar.apps.checkout.signals import post_payment, error_order
from oscar.core.compat import get_user_model
from oscar.core.loading import get_model

Notification = get_model("communication", "Notification")

# pylint: disable=unused-argument
@receiver(error_order)
def error_placing_order_view(sender, error, order_number, **kwargs):
    pass