from apps.webshop.shipping.tasks import update_shipping_zones_jsons_task
from core.loading import get_model
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


ShippingZona = get_model("shipping", "ShippingZona")


# pylint: disable=unused-argument
@receiver(post_save, sender=ShippingZona)
def update_shipping_zones_jsons(sender, instance, created, **kwargs):
    """
    Update 2 json file of shipping zones for webshop and dashboard
    """
    if settings.CELERY:
        update_shipping_zones_jsons_task.delay()
    else:
        update_shipping_zones_jsons_task.delay()
