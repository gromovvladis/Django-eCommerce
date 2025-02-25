from django.db import transaction
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
    if instance.source.reference in settings.CASH_PAYMENTS and not instance.cash_transactions.exists():
        order = instance.source.order
        store = order.store
        txn_type = instance.txn_type

        transaction.on_commit(
            lambda: (
                create_store_cash_transaction_task.delay(
                    instance.amount, order.id, instance.id, store.id, txn_type
                )
                if settings.CELERY
                else create_store_cash_transaction_task(
                    instance.amount, order.id, instance.id, store.id, txn_type
                )
            )
        )
