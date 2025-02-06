from decimal import Decimal

from django.db import models
from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.utils import get_default_currency
from oscar.models.fields import AutoSlugField
from oscar.templatetags.currency_filters import currency

from . import bankcards


class Transaction(models.Model):
    """
    A transaction for a particular payment source.

    These are similar to the payment events within the order app but model a
    slightly different aspect of payment.  Crucially, payment sources and
    transactions have nothing to do with the lines of the order while payment
    events do.

    For example:
    * A ``pre-auth`` with a bankcard gateway
    * A ``settle`` with a credit provider (see :py:mod:`django-oscar-accounts`)
    """

    source = models.ForeignKey(
        "payment.Source",
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Источник",
    )

    # We define some sample types but don't constrain txn_type to be one of
    # these as there will be domain-specific ones that we can't anticipate
    # here.
    PAYMENT, REFUND = "Payment", "Refund"
    txn_type = models.CharField("Тип", max_length=128, blank=True)

    amount = models.DecimalField("Сумма", decimal_places=2, max_digits=12)
    reference = models.CharField("Референс", max_length=128, blank=True)
    status = models.CharField("Статус", max_length=128, blank=True)

    is_included = models.BooleanField("Транзакция учтена в источнике", default=False)
    receipt = models.BooleanField("Чек ОФД", default=False)
    paid = models.BooleanField("Оплачено", default=False)
    refundable = models.BooleanField("Возврат возможен", default=False)

    payment_id = models.CharField("Код оплаты", max_length=128, blank=True)
    refund_id = models.CharField("Код возврата", max_length=128, blank=True)

    date_created = models.DateTimeField(
        "Дата создания", auto_now_add=True, db_index=True
    )

    def __str__(self):
        return ("%(type)s - %(amount).2f") % {
            "type": self.txn_type,
            "amount": self.amount,
        }

    class Meta:
        app_label = "payment"
        ordering = ["-date_created"]
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"


class Source(models.Model):
    """
    A source of payment for an order.

    This is normally a credit card which has been pre-authorised for the order
    amount, but some applications will allow orders to be paid for using
    multiple sources such as cheque, credit accounts, gift cards. Each payment
    source will have its own entry.

    This source object tracks how much money has been authorised, debited and
    refunded, which is useful when payment takes place in multiple stages.
    """

    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="sources",
        verbose_name="Заказ",
    )
    source_type = models.ForeignKey(
        "payment.SourceType",
        on_delete=models.CASCADE,
        related_name="sources",
        verbose_name="Тип источника",
    )
    currency = models.CharField("Валюта", max_length=12, default=get_default_currency)

    # Track the various amounts associated with this source
    amount_allocated = models.DecimalField(
        "Сумма для оплаты", decimal_places=2, max_digits=12, default=Decimal("0.00")
    )
    amount_debited = models.DecimalField(
        "Сумма оплачено", decimal_places=2, max_digits=12, default=Decimal("0.00")
    )
    amount_refunded = models.DecimalField(
        "Сумма возвращено", decimal_places=2, max_digits=12, default=Decimal("0.00")
    )

    # Reference number for this payment source.  This is often used to look up
    # a transaction model for a particular payment store.
    reference = models.CharField("Референс", max_length=255, blank=True)

    # refundable
    refundable = models.BooleanField("Возврат возможен?", blank=True)

    # paid
    paid = models.BooleanField("Оплачено", blank=True)

    # A dictionary of submission data that is stored as part of the
    # checkout process, where we need to pass an instance of this class around
    submission_data = None

    # We keep a list of deferred transactions that are only actually saved when
    # the source is saved for the first time
    deferred_txns = None

    class Meta:
        app_label = "payment"
        ordering = ["pk"]
        permissions = (
            ("full_access", "Полный доступ к источникам оплаты"),
            ("read", "Просматривать платежи и возвраты"),
            ("make_refund", "Остуществлять возвраты"),
        )
        verbose_name = "Источник оплаты"
        verbose_name_plural = "Источники оплаты"

    def __str__(self):
        description = "Сумма к оплате - %(amount)s способом оплаты - %(type)s" % {
            "amount": currency(self.amount_allocated, self.currency),
            "type": self.source_type,
        }
        if self.reference:
            description += " (%s)" % self.reference
        return description

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.deferred_txns:
            for txn in self.deferred_txns:
                self._create_transaction(*txn)

    def create_deferred_transaction(
        self,
        txn_type,
        amount,
        reference=None,
        status=None,
        paid=None,
        refundable=None,
        receipt=False,
        payment_id=None,
        refund_id=None,
    ):
        """
        Register the data for a transaction that can't be created yet due to FK
        constraints. This happens at checkout where create an payment source
        and a transaction but can't save them until the order model exists.
        """
        if self.deferred_txns is None:
            self.deferred_txns = []
        self.deferred_txns.append(
            (
                txn_type,
                amount,
                reference,
                status,
                paid,
                refundable,
                receipt,
                payment_id,
                refund_id,
            )
        )

    def _create_transaction(
        self,
        txn_type,
        amount,
        reference="",
        status="",
        paid=False,
        refundable=False,
        receipt=False,
        payment_id="",
        refund_id="",
    ):
        return self.transactions.create(
            txn_type=txn_type,
            amount=amount,
            reference=reference,
            status=status,
            paid=paid,
            refundable=refundable,
            receipt=receipt,
            payment_id=payment_id,
            refund_id=refund_id,
        )

    # =======
    # Actions
    # =======

    # PAYMENTS
    def allocate(
        self,
        amount,
        reference="",
        status="",
        paid="",
        refundable=True,
        receipt=False,
        payment_id="",
    ):
        """
        Convenience method for ring-fencing money against this source
        """
        self.amount_allocated += amount
        self.save()
        self._create_transaction(
            txn_type=Transaction.PAYMENT,
            amount=amount,
            reference=reference,
            status=status,
            paid=paid,
            refundable=refundable,
            receipt=receipt,
            payment_id=payment_id,
        )

    allocate.alters_data = True

    def debit(
        self,
        amount=None,
        reference="",
        status="",
        paid="",
        refundable=True,
        receipt=False,
        payment_id="",
    ):
        """
        Convenience method for recording debits against this source
        """
        if amount is None:
            amount = self.balance

        self.amount_debited += amount
        self.save()
        self._create_transaction(
            txn_type=Transaction.PAYMENT,
            amount=amount,
            reference=reference,
            status=status,
            paid=paid,
            refundable=refundable,
            receipt=receipt,
            payment_id=payment_id,
        )

    debit.alters_data = True

    def new_payment(
        self,
        amount=None,
        reference="",
        status="",
        paid="",
        refundable=True,
        receipt=False,
        payment_id="",
    ):
        """
        Добавление новой транзакции оплаты
        """
        receipt = receipt or False

        if amount is None:
            amount = self.balance

        trx = self._create_transaction(
            txn_type=Transaction.PAYMENT,
            amount=amount,
            reference=reference,
            status=status,
            paid=paid,
            refundable=refundable,
            receipt=receipt,
            payment_id=payment_id,
        )

        if status == "succeeded":
            self.amount_debited += amount
            self.paid = self.balance >= self.amount_allocated
            self.refundable = any(trx.refundable for trx in self.transactions.all())

        self.save()

        return trx

    new_payment.alters_data = True

    def update_payment(
        self,
        amount=None,
        reference="",
        status="",
        paid="",
        refundable=True,
        receipt=False,
        payment_id="",
    ):
        """
        Обновление существующей транзакции оплаты.
        """
        try:
            transaction = self.transactions.get(payment_id=payment_id)
            old_amount = transaction.amount

            fields_to_update = {
                "amount": amount,
                "reference": reference,
                "status": status,
                "paid": paid,
                "refundable": refundable,
                "receipt": receipt,
            }
            updated_fields = {
                field: new_value
                for field, new_value in fields_to_update.items()
                if getattr(transaction, field) != new_value
            }

            if updated_fields:
                for field, value in updated_fields.items():
                    setattr(transaction, field, value)
                transaction.save()

            if status == "succeeded":
                transaction_is_new = not transaction.is_included
                amount_delta = (
                    transaction.amount - old_amount
                    if not transaction_is_new
                    else transaction.amount
                )

                if transaction_is_new or updated_fields:
                    self.amount_debited += amount_delta
                    self.paid = self.balance >= self.amount_allocated
                    self.refundable = self.transactions.filter(refundable=True).exists()
                    self.save()

                    if transaction_is_new:
                        transaction.is_included = True
                        transaction.save()

            return bool(updated_fields)

        except self.transactions.model.DoesNotExist:
            return self.new_payment(
                amount=amount,
                reference=reference,
                status=status,
                paid=paid,
                refundable=refundable,
                receipt=receipt,
                payment_id=payment_id,
            )

    update_payment.alters_data = True

    # REFUND
    def refund(
        self,
        amount,
        reference="",
        status="",
        paid="",
        refundable=False,
        receipt=False,
        refund_id="",
    ):
        """
        Convenience method for recording refunds against this source
        """
        if self.refundable:
            self.amount_refunded += amount
            self.save()
            self._create_transaction(
                txn_type=Transaction.REFUND,
                amount=amount,
                reference=reference,
                status=status,
                paid=paid,
                refundable=refundable,
                receipt=receipt,
                refund_id=refund_id,
            )

    refund.alters_data = True

    def new_refund(
        self,
        amount=None,
        reference="",
        status="",
        paid=False,
        refundable=False,
        receipt=False,
        refund_id="",
    ):
        """
        Добавление новой транзакции возврата
        """
        receipt = receipt or False

        if amount is None:
            amount = self.balance

        trx = self._create_transaction(
            txn_type=Transaction.REFUND,
            amount=amount,
            reference=reference,
            status=status,
            paid=paid,
            refundable=refundable,
            receipt=receipt,
            refund_id=refund_id,
        )

        if status == "succeeded":
            self.amount_refunded += amount
            self.paid = self.balance >= self.amount_allocated
            self.refundable = any(trx.refundable for trx in self.transactions.all())

        self.save()

        return trx

    new_refund.alters_data = True

    def update_refund(
        self,
        amount=None,
        reference="",
        status="",
        paid=False,
        refundable=False,
        receipt=False,
        refund_id="",
    ):
        """
        Обновление существующей транзакции возврата.
        """
        try:
            transaction = self.transactions.get(refund_id=refund_id)
            old_amount = transaction.amount

            # Обновляем только измененные поля
            fields_to_update = {
                "amount": amount,
                "reference": reference,
                "status": status,
                "paid": paid,
                "refundable": refundable,
                "receipt": receipt,
            }
            updated_fields = {
                field: new_value
                for field, new_value in fields_to_update.items()
                if getattr(transaction, field) != new_value
            }

            if updated_fields:
                for field, value in updated_fields.items():
                    setattr(transaction, field, value)
                transaction.save()

            if status == "succeeded":
                transaction_is_new = not transaction.is_included
                amount_delta = (
                    transaction.amount + old_amount
                    if transaction_is_new
                    else transaction.amount
                )

                if transaction_is_new or updated_fields:
                    self.amount_refunded -= amount_delta
                    self.paid = self.balance >= self.amount_allocated
                    self.refundable = self.transactions.filter(refundable=True).exists()
                    self.save()

                    if transaction_is_new:
                        transaction.is_included = True
                        transaction.save()

            return bool(updated_fields)

        except self.transactions.model.DoesNotExist:
            return self.new_refund(
                amount=amount,
                reference=reference,
                status=status,
                paid=paid,
                refundable=refundable,
                receipt=receipt,
                refund_id=refund_id,
            )

    update_refund.alters_data = True

    # ==========
    # Properties
    # ==========

    @property
    def balance(self):
        """
        Return the balance of this source
        """
        return self.amount_debited - self.amount_refunded

    @property
    def amount_available_for_refund(self):
        """
        Return the amount available to be refunded
        """
        return self.amount_debited - self.amount_refunded


class SourceType(models.Model):
    """
    A type of payment source.

    This could be an external store like PayPal or DataCash,
    or an internal source such as a managed account.
    """

    name = models.CharField("Имя", max_length=128, db_index=True)
    code = AutoSlugField(
        "Код",
        max_length=128,
        populate_from="name",
        unique=True,
        help_text="Это используется в формах для идентификации этого типа источника.",
    )

    class Meta:
        app_label = "payment"
        ordering = ["name"]
        verbose_name = "Тип источника оплаты"
        verbose_name_plural = "Типы источников оплаты"

    def __str__(self):
        return self.name


class Bankcard(models.Model):
    """
    Model representing a user's bankcard.  This is used for two purposes:

        1.  The bankcard form will return an instance of this model that can be
            used with payment gateways.  In this scenario, the instance will
            have additional attributes (start_date, issue_number, :abbr:`ccv (Card Code Verification)`) that
            payment gateways need but that we don't save.

        2.  To keep a record of a user's bankcards and allow them to be
            re-used.  This is normally done using the 'store reference'.

    .. warning::

        Some of the fields of this model (name, expiry_date) are considered
        "cardholder data" under PCI DSS v2. Hence, if you use this model and
        store those fields then the requirements for PCI compliance will be
        more stringent.
    """

    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bankcards",
        verbose_name="Пользователь",
    )
    card_type = models.CharField("Тип карты", max_length=128)

    # Often you don't actually need the name on the bankcard
    name = models.CharField("Имя", max_length=255, blank=True)

    # We store an obfuscated version of the card number, just showing the last
    # 4 digits.
    number = models.CharField("Номер", max_length=32)

    # We store a date even though only the month is visible.  Bankcards are
    # valid until the last day of the month.
    expiry_date = models.DateField("Дата истечения срока действия")

    # Temporary data not persisted to the DB
    start_date = None
    issue_number = None
    ccv = None

    def __str__(self):
        return ("%(card_type)s %(number)s (Срок действия истекает: %(expiry)s)") % {
            "card_type": self.card_type,
            "number": self.number,
            "expiry": self.expiry_month(),
        }

    def __init__(self, *args, **kwargs):
        # Pop off the temporary data
        self.start_date = kwargs.pop("start_date", None)
        self.issue_number = kwargs.pop("issue_number", None)
        self.ccv = kwargs.pop("ccv", None)
        super().__init__(*args, **kwargs)

        # Initialise the card-type
        if self.id is None:
            self.card_type = bankcards.bankcard_type(self.number)
            if self.card_type is None:
                self.card_type = "Unknown card type"

    class Meta:
        app_label = "payment"
        verbose_name = "Банковская карта"
        verbose_name_plural = "Банковские карты"

    def save(self, *args, **kwargs):
        if not self.number.startswith("X"):
            self.prepare_for_save()
        super().save(*args, **kwargs)

    def prepare_for_save(self):
        # This is the first time this card instance is being saved.  We
        # remove all sensitive data
        self.number = "XXXX-XXXX-XXXX-%s" % self.number[-4:]
        self.start_date = self.issue_number = self.ccv = None

    @property
    def cvv(self):
        return self.ccv

    @property
    def obfuscated_number(self):
        return "XXXX-XXXX-XXXX-%s" % self.number[-4:]

    # pylint: disable=W0622
    def start_month(self, format="%m/%y"):
        return self.start_date.strftime(format)

    # pylint: disable=W0622
    def expiry_month(self, format="%m/%y"):
        return self.expiry_date.strftime(format)
