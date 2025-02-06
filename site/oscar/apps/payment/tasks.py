import logging
from celery import shared_task

from oscar.core.loading import get_model

logger = logging.getLogger("oscar.payment")

Transaction = get_model("payment", "Transaction")
StoreCashTransaction = get_model("store", "StoreCashTransaction")


@shared_task
def create_store_cash_transaction_task(txn_id, *args, **kwargs):
    try:
        txn = Transaction.objects.select_related(
            "source", "source__order", "source__order__store"
        ).get(id=txn_id)
        if txn.source.reference == "CASH":
            order = txn.source.order
            store = order.store
            StoreCashTransaction.objects.create(
                store=store,
                order=order,
                sum=txn.amount,
                description=(
                    "Оплата наличными заказа"
                    if txn.txn_type == "Payment"
                    else "Возврат наличными заказа"
                ),
                type=(
                    StoreCashTransaction.PAYMENT
                    if txn.txn_type == "Payment"
                    else StoreCashTransaction.REFUND
                ),
            )

    except Exception as err:
        logger.error(
            "Ошибка при создании внесения / иъятия наличных из магазина StoreCashTransaction.",
            err,
        )
