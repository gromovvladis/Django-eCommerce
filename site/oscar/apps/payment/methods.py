import uuid
import logging
from yookassa import Refund
from yookassa import Payment

from yookassa.domain.models.receipt import Receipt
from yookassa.domain.common.confirmation_type import ConfirmationType
from yookassa.domain.request.payment_request_builder import PaymentRequestBuilder
from yookassa.domain.request import RefundRequestBuilder
from yookassa.domain.response.refund_response import RefundResponse
from yookassa.domain.response.payment_response import PaymentResponse

from django.urls import reverse_lazy
from django.conf import settings
from django.contrib import messages

from oscar.apps.order.models import PaymentEventQuantity
from oscar.apps.payment.models import Source, Transaction
from oscar.apps.order.models import Order, PaymentEvent, PaymentEventType
from oscar.apps.payment.exceptions import (
    UnableToRefund,
    UnableToTakePayment,
)

logger = logging.getLogger("oscar.payment")
thank_you_url = reverse_lazy("checkout:thank-you")


class PaymentManager:
    """
    Payment method will be chosen.
    """

    def __init__(self, source_reference=None, user=None):
        self.source_reference = source_reference
        self.user = user

    def get_method(self):
        if self.source_reference == "ONLINECARD":
            return Yoomoney(self.source_reference, self.user)
        if self.source_reference == "ELECTRON":
            return CardOffline(self.source_reference, self.user)
        else:
            return Cash(self.source_reference, self.user)

    @classmethod
    def get_sources(self, pk):
        return Source.objects.filter(order_id=pk).select_related("order")


class PaymentMethod(object):
    def __init__(self, payment_method, user):
        self.success_url = f"https://{settings.ALLOWED_HOSTS[0]}{thank_you_url}"
        self.payment_method = payment_method
        self.user = user

    def pay(self, order, source, amount=None, email=None):
        raise NotImplementedError("A PaymentMethod must define a pay method ")

    def refund(self, transaction, amount=None):
        raise NotImplementedError("A PaymentMethod must define a refund method ")

    def add_event(
        self, order, transaction, transaction_status_list=None, updated=False
    ):
        event_type, __ = PaymentEventType.objects.get_or_create(
            name=self.get_status(transaction_status_list, transaction.status, updated)
        )
        event = PaymentEvent(
            event_type=event_type,
            amount=transaction.amount,
            reference=transaction.event_reference(),
        )
        event.order = order
        event.save()
        for line in order.lines.all():
            PaymentEventQuantity.objects.create(
                event=event, line=line, quantity=line.quantity
            )

    def get_status(self, status_list, tnx_status, updated):
        if updated:
            return "Обновление транзакции"
        elif tnx_status == "succeeded":
            return status_list["succeeded"]
        elif tnx_status == "canceled":
            return status_list["canceled"]
        elif tnx_status == "pending":
            return status_list["pending"]

    def change_order_status(self, tnx_status, tnx_type, order):
        current_status = order.status

        if tnx_type == "payment":
            status_list = self.payment_status_order()
        elif tnx_type == "refund":
            status_list = self.refund_status_order()
        else:
            logger.error(
                "Неизвестный тип транзакции. Транзакция: {1}, Заказ: {2}".format(
                    tnx_type, order.number
                )
            )
            return messages.error(self.request, "Неизвестный тип транзакции.")

        new_status = self.get_status(
            status_list=status_list, tnx_status=tnx_status, updated=False
        )

        if new_status and new_status != current_status:
            order.set_status(new_status)

    def get_method(self):
        return self.payment_method

    def get_transactions(self, payment_source):
        return Transaction.objects.filter(source_id=payment_source.id)

    def payment_status_list(self):
        return settings.PAYMENT_STATUS

    def refund_status_list(self):
        return settings.REFUND_STATUS

    def payment_status_order(self):
        return settings.PAYMENT_ORDER_STATUS

    def refund_status_order(self):
        return settings.REFUND_ORDER_STATUS

    def __str__(self) -> str:
        return self.payment_method


class Yoomoney(PaymentMethod):

    vats = {
        "NO_VAT": 1,
        "VAT_0": 2,
        "VAT_10": 3,
        "VAT_10_110": 4,
        "VAT_18": 5,
        "VAT_18_118": 6,
    }

    unit_codes = {
        "шт": "piece",
        "г": "gram",
        "кг": "kilogram",
        "т": "ton",
        "см": "centimeter",
        "дм": "decimeter",
        "м": "meter",
        "см²": "square_centimeter",
        "дм²": "square_decimeter",
        "м²": "square_meter",
        "мл": "milliliter",
        "л": "liter",
        "м³": "cubic_meter",
        "кВт·ч": "kilowatt_hour",
        "Гкал": "gigacalorie",
        "сутки": "day",
        "день": "day",
        "час": "hour",
        "минута": "minute",
        "секунда": "second",
        "КБ": "kilobyte",
        "МБ": "megabyte",
        "ГБ": "gigabyte",
        "ТБ": "terabyte",
    }

    def pay(self, order, source, amount=None, email=None):
        try:
            if amount is None:
                amount_value = order.total
                currency = order.currency
            else:
                amount_value = amount.money
                currency = amount.currency

            if email is None:
                email = order.user.email

            receipt = Receipt()
            receipt.customer = {
                "phone": str(order.user.username),
                **({"email": email} if email else {}),
            }
            receipt.tax_system_code = 4
            receipt.items = self._receipt_items(order)

            builder = PaymentRequestBuilder()
            builder.set_amount(
                {"value": amount_value, "currency": currency}
            ).set_confirmation(
                {"type": ConfirmationType.REDIRECT, "return_url": self.success_url}
            ).set_capture(
                True
            ).set_description(
                "Заказ №" + str(order.number)
            ).set_metadata(
                {"orderNumber": order.number}
            ).set_receipt(
                receipt
            ).set_merchant_customer_id(
                order.user.id
            )
            request = builder.build()
            payment = Payment.create(request, uuid.uuid4())
            self.create_payment_transaction(payment, source)

        except Exception as e:
            raise UnableToTakePayment(f"Ошибка создания платежа ЮКасса {e}")

        return payment

    def update_payment(self, payment, source):
        payment_transactions = self.get_transactions(source).filter(txn_type="Payment")

        if payment.id in payment_transactions.values_list("payment_id", flat=True):
            return self.update_payment_transaction(payment, source)
        else:
            self.create_payment_transaction(payment, source)
            return True

    def create_payment_transaction(self, payment, source):
        if payment.payment_method:
            reference = payment.payment_method.title
        elif self.user:
            reference = "Сотрудник " + str(self.user.username)
        else:
            reference = str(source.reference) + " Payment"

        transaction = source.new_payment(
            amount=payment.amount.value,
            reference=reference,
            status=payment.status,
            paid=payment.paid,
            refundable=payment.refundable,
            receipt=payment.receipt_registration,
            payment_id=payment.id,
        )

        self.add_event(
            order=source.order,
            transaction=transaction,
            transaction_status_list=self.payment_status_list(),
        )

    def update_payment_transaction(self, payment, source):
        if payment.payment_method:
            reference = payment.payment_method.title
        else:
            reference = str(source.reference) + " Payment"

        transaction = source.update_payment(
            amount=payment.amount.value,
            reference=reference,
            paid=payment.paid,
            refundable=payment.refundable,
            status=payment.status,
            receipt=payment.receipt_registration or False,
            payment_id=payment.id,
        )

        if transaction:
            self.add_event(order=source.order, transaction=transaction, updated=True)
            return True

        return False

    def get_payment_api(self, pay_id):
        try:
            responce = Payment.find_one(pay_id)
        except Exception:
            return None

        return responce

    def refund(self, transaction, amount=None):
        try:
            payment_id = transaction.payment_id
            if payment_id:
                order = transaction.source.order
                email = order.user.email

                if amount is None:
                    amount = transaction.amount

                receipt = Receipt()
                receipt.customer = {
                    "phone": str(order.user.username),
                    **({"email": email} if email else {}),
                }
                receipt.tax_system_code = 4
                receipt.items = self._receipt_items(order)

                item_list = []
                for line in order.lines.all():
                    item = {
                        "description": line.name,
                        "quantity": line.quantity,
                        "amount": {
                            "value": line.line_price,
                            "currency": order.currency,
                        },
                        "vat_code": 4,
                    }
                    item_list.append(item)

                receipt.items = item_list

                builder = RefundRequestBuilder()
                builder.set_payment_id(payment_id).set_description(
                    "Возврат по заказу №" + str(order.number)
                ).set_amount(
                    {"value": amount, "currency": transaction.source.currency}
                ).set_receipt(
                    receipt
                )
                request = builder.build()
                refund = Refund.create(request)
                transaction.refundable = False
                transaction.save()
                self.create_refund_transaction(refund, transaction.source, amount)
        except Exception as e:
            try:
                error = e.response.content
            except Exception as e:
                error = e
            raise UnableToRefund(f"Невозможно произвести возврат. Причина: {error}")

        return refund

    def update_refund(self, refund, source):
        refund_transactions = self.get_transactions(source).filter(txn_type="Refund")

        if refund.id in refund_transactions.values_list("refund_id", flat=True):
            self.create_refund_transaction(refund, source)
            return True
        else:
            return self.update_refund_transaction(refund, source)

    def create_refund_transaction(self, refund, source, amount=None):
        if amount is None:
            amount = refund.amount.value

        if self.user:
            reference = "Сотрудник " + str(self.user.username)
        else:
            reference = str(source.reference) + " Refund"

        transaction = source.new_refund(
            amount=amount,
            reference=reference,
            status=refund.status,
            receipt=refund.receipt_registration,
            refund_id=refund.id,
        )

        self.add_event(
            order=source.order,
            transaction=transaction,
            transaction_status_list=self.refund_status_list(),
        )

    def update_refund_transaction(self, refund, source):
        if self.user:
            reference = "Сотрудник " + str(self.user.username)
        else:
            reference = str(source.reference) + " Refund"

        transaction = source.update_refund(
            amount=refund.amount.value,
            reference=reference,
            status=refund.status,
            receipt=refund.receipt_registration or False,
            refund_id=refund.id,
        )

        if transaction:
            self.add_event(order=source.order, transaction=transaction, updated=True)
            return True

        return False

    def get_refund_api(self, refund_id):
        try:
            responce = Refund.find_one(refund_id)
        except Exception:
            return None

        return responce

    # Helpers

    def update(self, source, payment=None, refund=None):
        refund_updated = False
        payment_updated = False

        if isinstance(refund, RefundResponse):
            refund_updated = self.update_refund(refund, source)

        if isinstance(payment, PaymentResponse):
            payment_updated = self.update_payment(payment, source)

        if refund_updated:
            self.change_order_status(
                tnx_status=refund.status,
                tnx_type="refund",
                order=source.order,
            )
        elif payment_updated:
            self.change_order_status(
                tnx_status=payment.status,
                tnx_type="payment",
                order=source.order,
            )

    def _receipt_items(self, order):
        item_list = []
        for line in order.lines.all():
            item = {
                "description": line.get_full_name(),
                "quantity": line.quantity,
                "amount": {
                    "value": line.line_price,
                    "currency": order.currency,
                },
                "measure": self.unit_codes.get(
                    line.product.get_product_class().measure_name, "piece"
                ),
                "payment_subject": "commodity",
                "payment_mode": "full_payment",
                "vat_code": self.vats.get(line.tax_code, 6),
            }
            item_list.append(item)

        if order.shipping > 0:
            item_list.append(
                {
                    "description": "Доставка",
                    "quantity": 1,
                    "amount": {
                        "value": order.shipping,
                        "currency": order.currency,
                    },
                    "measure": "piece",
                    "payment_subject": "service",
                    "payment_mode": "full_payment",
                    "vat_code": 6,
                }
            )

        return item_list


class Cash(PaymentMethod):
    def pay(self, order, source, amount=None, email=None):
        if amount is None:
            amount_value = order.total
        else:
            amount_value = amount.money

        self.create_payment_transaction(order, source, amount_value)

    def create_payment_transaction(self, order, source, amount):
        if self.user:
            reference = "Сотрудник " + str(self.user.username)
        else:
            reference = str(source.reference) + " Payment"

        transaction = source.new_payment(
            amount=amount,
            reference=reference,
            status="succeeded",
        )

        self.add_event(
            order=order,
            transaction=transaction,
            transaction_status_list=self.payment_status_list(),
        )

    def refund(self, transaction, amount=None):
        transaction.refundable = False
        transaction.save()

        if amount is None:
            amount = transaction.amount

        self.create_refund_transaction(transaction.source, amount)
        return transaction

    def create_refund_transaction(self, source, amount):
        if self.user:
            reference = "Сотрудник " + str(self.user.username)
        else:
            reference = str(source.reference) + " Refund"

        transaction = source.new_refund(
            amount=amount,
            reference=reference,
            status="succeeded",
        )

        self.add_event(
            order=source.order,
            transaction=transaction,
            transaction_status_list=self.refund_status_list(),
        )


class CardOffline(Cash):
    pass
