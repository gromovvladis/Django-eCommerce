from django.dispatch import receiver
from apps.webshop.checkout.signals import error_order
from core.loading import get_model

Notification = get_model("communication", "Notification")


# pylint: disable=unused-argument
@receiver(error_order)
def error_placing_order_view(sender, error, order_number, **kwargs):
    pass
