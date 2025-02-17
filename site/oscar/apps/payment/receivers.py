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
    if instance.source.reference in settings.CASH_PAYMENTS:
        order = instance.source.order
        store = order.store
        txn_type = instance.txn_type
        if settings.CELERY:
            create_store_cash_transaction_task.delay(
                instance.amount, order.id, store.id, txn_type
            )
        else:
            create_store_cash_transaction_task(
                instance.amount, order.id, store.id, txn_type
            )
