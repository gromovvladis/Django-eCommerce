import logging
from celery import shared_task

from oscar.core.loading import get_model

Transaction = get_model("payment", "Transaction")
StoreCashTransaction = get_model("store", "StoreCashTransaction")

logger = logging.getLogger("oscar.payment")


@shared_task
def create_store_cash_transaction_task(
    sum, order_id, transaction_id, store_id, txn_type, *args, **kwargs
):
    try:
        StoreCashTransaction.objects.create(
            sum=sum,
            order_id=order_id,
            transaction_id=transaction_id,
            store_id=store_id,
            description=(
                "Оплата наличными заказа"
                if txn_type == "Payment"
                else "Возврат наличными заказа"
            ),
            type=(
                StoreCashTransaction.PAYMENT
                if txn_type == "Payment"
                else StoreCashTransaction.REFUND
            ),
        )

    except Exception as err:
        logger.error(
            "Ошибка при создании внесения / иъятия наличных из магазина StoreCashTransaction.",
            err,
        )
