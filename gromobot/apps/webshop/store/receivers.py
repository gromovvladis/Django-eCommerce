from core.loading import get_model
from django.db.models.signals import post_save
from django.dispatch import receiver

StockAlert = get_model("store", "StockAlert")
StockRecord = get_model("store", "StockRecord")


# pylint: disable=unused-argument
@receiver(post_save, sender=StockRecord)
def update_stock_alerts(sender, instance, created, **kwargs):
    """
    Update low-stock alerts
    """
    if created or kwargs.get("raw", False):
        return
    stockrecord = instance
    try:
        alert = StockAlert.objects.get(stockrecord=stockrecord, status=StockAlert.OPEN)
    except StockAlert.DoesNotExist:
        alert = None

    if stockrecord.is_below_threshold and not alert:
        StockAlert.objects.create(stockrecord=stockrecord)
    elif not stockrecord.is_below_threshold and alert:
        alert.close()


# @receiver(post_save, sender=StockRecord)
# def update_cache_product(sender, instance, created, **kwargs):
#     if settings.DEBUG:
#         update_cache_product_task.delay(product_id=instance.product_id, store_id=instance.store_id)
