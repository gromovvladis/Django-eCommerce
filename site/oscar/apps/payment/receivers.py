from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save

from oscar.apps.payment.tasks import create_store_cash_transaction_task
from oscar.core.loading import get_model

Transaction = get_model("payment", "Transaction")


@receiver(post_save, sender=Transaction)
def transaction_created(sender, instance, created, **kwargs):
    """
    Запускает задачу при обновлении объекта Source.
    """
    if settings.DEBUG:
        create_store_cash_transaction_task(instance.id)
    else:
        create_store_cash_transaction_task.delay(instance.id)
