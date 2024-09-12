# pylint: disable=F0002
import logging
from decimal import Decimal as D

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.core.signing import BadSignature, Signer
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.timezone import now
from oscar.apps.order.signals import order_line_status_changed, order_status_changed
from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.loading import get_model
from oscar.core.utils import get_default_currency
from oscar.models.fields import AutoSlugField

from . import exceptions

logger = logging.getLogger("oscar.order")


class AbstractOrder(models.Model):
    """
    The main order model
    """

    number = models.CharField(
        "Номер заказа", max_length=128, db_index=True, unique=True
    )

    # We track the site that each order is placed within
    # site = models.CharField(verbose_name="Источник заказа", null=True, blank=True, max_length=128)

    basket = models.ForeignKey(
        "basket.Basket",
        verbose_name="Корзина",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    # Orders can be placed without the user authenticating so we don't always
    # have a customer ID.
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name="orders",
        null=True,
        blank=True,
        verbose_name="Пользователь",
        on_delete=models.SET_NULL,
    )

    # Total price looks like it could be calculated by adding up the
    # prices of the associated lines, but in some circumstances extra
    # order-level charges are added and so we need to store it separately
    currency = models.CharField(
        "Валюта", max_length=12, default=get_default_currency
    )
    total = models.DecimalField(
        "Сумма заказа", decimal_places=2, max_digits=12
    )

    # Shipping charges
    shipping = models.DecimalField(
        "Плата за доставку", decimal_places=2, max_digits=12, default=0
    )

    # Not all lines are actually shipped (such as downloads), hence shipping
    # address is not mandatory.
    shipping_address = models.ForeignKey(
        "order.ShippingAddress",
        null=True,
        blank=True,
        verbose_name="Адрес доставки",
        on_delete=models.SET_NULL,
    )

    shipping_method = models.CharField("Способ доставки", max_length=128, blank=True)

    # Use this field to indicate that an order is on hold / awaiting payment
    status = models.CharField("Статус", max_length=100, blank=True)

    # Index added to this field for reporting
    date_placed = models.DateTimeField(db_index=True, editable=False)

    # Date and time of order
    order_time = models.DateTimeField(db_index=True, blank=True)

    # Date and time of finish order
    date_finish = models.DateTimeField(db_index=True, blank=True, null=True)

    has_review = models.BooleanField(db_index=True, default=False)

    is_open = models.BooleanField("Заказ просмотрен", default=False, db_index=True)

    #: Order status pipeline.  This should be a dict where each (key, value) #:
    #: corresponds to a status and a list of possible statuses that can follow
    #: that one.
    pipeline = getattr(settings, "OSCAR_ORDER_STATUS_PIPELINE", {})

    #: Order status cascade pipeline.  This should be a dict where each (key,
    #: value) pair corresponds to an *order* status and the corresponding
    #: *line* status that needs to be set when the order is set to the new
    #: status
    cascade = getattr(settings, "OSCAR_ORDER_STATUS_CASCADE", {})

    @classmethod
    def all_statuses(cls):
        """
        Return all possible statuses for an order
        """
        return list(cls.pipeline.keys())

    def available_statuses(self):
        """
        Return all possible statuses that this order can move to
        """
        return self.pipeline.get(self.status, ())

    def set_status(self, new_status):
        """
        Set a new status for this order.

        If the requested status is not valid, then ``InvalidOrderStatus`` is
        raised.
        """
        if new_status == self.status:
            return

        old_status = self.status

        if new_status not in self.available_statuses():
            raise exceptions.InvalidOrderStatus(
                (
                    "'%(new_status)s' недействительный статус для заказа %(number)s"
                    " (текущий статус: '%(status)s')"
                )
                % {
                    "new_status": new_status,
                    "number": self.number,
                    "status": self.status,
                }
            )
        self.status = new_status
        if new_status in self.cascade:
            new_line_status = self.cascade[new_status]
            for line in self.lines.all():
                if new_line_status in line.available_statuses():
                    line.status = new_line_status
                    line.save()
        
        if new_status in ["Отменен", "Завершен"]:
            self.date_finish = now()
        
        self.save()

        # Send signal for handling status changed
        order_status_changed.send(
            sender=self,
            order=self,
            old_status=old_status,
            new_status=new_status,
        )

        self._create_order_status_change(old_status, new_status)

    set_status.alters_data = True

    def _create_order_status_change(self, old_status, new_status):
        # Not setting the status on the order as that should be handled before
        self.status_changes.create(old_status=old_status, new_status=new_status)
        
    def open(self):
        self.is_open = True
        self.save()

    @property
    def basket_total_before_discounts(self):
        """
        Return basket total but before discounts are applied
        """
        result = self.lines.aggregate(total=Sum("line_price_before_discounts"))
        return result["total"]

    @property
    def basket_total(self):
        """
        Return basket total
        """
        return self.total - self.shipping - self.surcharge

    @property
    def total_before_discounts(self):
        return self.basket_total_before_discounts + self.shipping

    @property
    def total_discount(self):
        """
        The amount of discount this order received
        """
        discount = D("0.00")
        for line in self.lines.all():
            discount += line.discount
        return discount

    @property
    def surcharge(self):
        return sum(charge.money for charge in self.surcharges.all())

    @property
    def num_lines(self):
        return self.lines.count()

    @property
    def num_items(self):
        """
        Returns the number of items in this order.
        """
        num_items = 0
        for line in self.lines.all():
            num_items += line.quantity
        return num_items


    @property
    def shipping_status(self):
        """Return the last complete shipping event for this order."""

        # As safeguard against identical timestamps, also sort by the primary
        # key. It's not recommended to rely on this behaviour, but in practice
        # reasonably safe if PKs are not manually set.
        events = self.shipping_events.order_by("-date_created", "-pk").all()
        if not len(events):
            return ""

        # Collect all events by event-type
        event_map = {}
        for event in events:
            event_name = event.event_type.name
            if event_name not in event_map:
                event_map[event_name] = []
            event_map[event_name].extend(list(event.line_quantities.all()))

        # Determine last complete event
        status = "В процессе выполнения"
        for event_name, event_line_quantities in event_map.items():
            if self._is_event_complete(event_line_quantities):
                return event_name
        return status

    @property
    def has_shipping_discounts(self):
        return len(self.shipping_discounts) > 0

    @property
    def shipping_before_discounts(self):
        # We can construct what shipping would have been before discounts by
        # adding the discounts back onto the final shipping charge.
        total = D("0.00")
        for discount in self.shipping_discounts:
            total += discount.amount
        return self.shipping + total

    def _is_event_complete(self, event_quantities):
        # Form map of line to quantity
        event_map = {}
        for event_quantity in event_quantities:
            line_id = event_quantity.line_id
            event_map.setdefault(line_id, 0)
            event_map[line_id] += event_quantity.quantity

        for line in self.lines.all():
            if event_map.get(line.pk, 0) != line.quantity:
                return False
        return True

    class Meta:
        abstract = True
        app_label = "order"
        ordering = ["-date_placed"]
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return "#%s" % (self.number,)

    def verification_hash(self):
        signer = Signer(salt="oscar.apps.order.Order")
        return signer.sign(self.number)

    def check_verification_hash(self, hash_to_check):
        """
        Checks the received verification hash against this order number.
        Returns False if the verification failed, True otherwise.
        """
        signer = Signer(salt="oscar.apps.order.Order")
        try:
            signed_number = signer.unsign(hash_to_check)
        except BadSignature:
            return False

        return constant_time_compare(signed_number, self.number)

    @property
    def email(self):
        if self.user:
            return self.user.email
        
    @property
    def client_note(self):
        note = self.notes.get(note_type="Комментарий к заказу")
        if note:
            return note.message   

    @property
    def basket_discounts(self):
        # This includes both offer- and voucher- discounts.  For orders we
        # don't need to treat them differently like we do for baskets.
        return self.discounts.filter(category=AbstractOrderDiscount.BASKET)

    @property
    def shipping_discounts(self):
        return self.discounts.filter(category=AbstractOrderDiscount.SHIPPING)

    @property
    def post_order_actions(self):
        return self.discounts.filter(category=AbstractOrderDiscount.DEFERRED)

    def set_date_placed_default(self):
        if self.date_placed is None:
            self.date_placed = now()

    def save(self, *args, **kwargs):
        # Ensure the date_placed field works as it auto_now_add was set. But
        # this gives us the ability to set the date_placed explicitly (which is
        # useful when importing orders from another system).
        self.set_date_placed_default()
        super().save(*args, **kwargs)


class AbstractOrderNote(models.Model):
    """
    A note against an order.

    This are often used for audit purposes too.  IE, whenever an admin
    makes a change to an order, we create a note to record what happened.
    """

    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name="Заказ",
    )

    # These are sometimes programatically generated so don't need a
    # user everytime
    user = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, verbose_name="Пользователь"
    )

    # We allow notes to be classified although this isn't always needed
    USER, MANAGER, STAFF, SYSTEM = "Комментарий к заказу", "Заметка менеджера", "Заметка персоналу", "Системная заметка"
    TYPE_CHOICES = (
        (USER, "Комментарий к заказу"),
        (MANAGER, "Заметка менеджера"),
        (STAFF, "Заметка персоналу"),
        (SYSTEM, "Системная заметка"),
    )
    note_type = models.CharField("Тип примечания", choices=TYPE_CHOICES, default=MANAGER, max_length=30, blank=True)

    message = models.TextField("Сообщение")
    date_created = models.DateTimeField("Дата создания", auto_now_add=True)
    date_updated = models.DateTimeField("Дата изменения", auto_now=True)

    # Notes can only be edited for 5 minutes after being created
    editable_lifetime = 300

    class Meta:
        abstract = True
        app_label = "order"
        ordering = ["-date_updated"]
        verbose_name = "Примечание к заказу"
        verbose_name_plural = "Примечания к заказам"

    def __str__(self):
        return "'%s' (%s)" % (self.message[0:50], self.user)

    def is_editable(self):
        if self.note_type == self.SYSTEM:
            return False
        delta = timezone.now() - self.date_updated
        return delta.seconds < self.editable_lifetime


class AbstractOrderStatusChange(models.Model):
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="status_changes",
        verbose_name="Изменение статуса заказа",
    )
    old_status = models.CharField("Старый статус", max_length=100, blank=True)
    new_status = models.CharField("Новый статус", max_length=100, blank=True)
    date_created = models.DateTimeField(
        "Дата создания", auto_now_add=True, db_index=True
    )

    class Meta:
        abstract = True
        app_label = "order"
        verbose_name = "Изменение статуса заказа"
        verbose_name_plural = "Изменения статусов заказов"
        ordering = ["-date_created"]

    def __str__(self):
        return (
            "%(order)s изменил статус с %(old_status)s на %(new_status)s"
        ) % {
            "order": self.order,
            "old_status": self.old_status,
            "new_status": self.new_status,
        }


class AbstractCommunicationEvent(models.Model):
    """
    An order-level event involving a communication to the customer, such
    as an confirmation email being sent.
    """

    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="communication_events",
        verbose_name="Заказ",
    )
    event_type = models.ForeignKey(
        "communication.CommunicationEventType",
        on_delete=models.CASCADE,
        verbose_name="Тип события",
    )
    date_created = models.DateTimeField("Дата создания", auto_now_add=True, db_index=True)

    class Meta:
        abstract = True
        app_label = "order"
        verbose_name = "Событие связи"
        verbose_name_plural = "События связи"
        ordering = ["-date_created"]

    def __str__(self):
        return ("'%(type)s' событие заказа #%(number)s") % {
            "type": self.event_type.name,
            "number": self.order.number,
        }


# LINES
class AbstractLine(models.Model):
    """
    An order line
    """

    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name="Заказ",
    )

    # PARTNER INFORMATION
    # -------------------
    # We store the partner and various detail their SKU and the title for cases
    # where the product has been deleted from the catalogue (but we still need
    # the data for reporting).  We also store the partner name in case the
    # partner gets deleted at a later date.

    partner = models.ForeignKey(
        "partner.Partner",
        related_name="order_lines",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Точка продажи",
    )
    partner_name = models.CharField("Название точки продажи", max_length=128, blank=True)
    partner_sku = models.CharField("Артикул в точке продажи", max_length=128)

    # A line reference is the ID that a partner uses to represent this
    # particular line (it's not the same as a SKU).
    partner_line_reference = models.CharField(
        "Код точки продажи",
        max_length=128,
        blank=True,
        help_text=(
            "Это номер позиции, который партнер использует в своей системе."
        ),
    )
    partner_line_notes = models.TextField("Примечание точки продажи", blank=True)

    # We keep a link to the stockrecord used for this line which allows us to
    # update stocklevels when it ships
    stockrecord = models.ForeignKey(
        "partner.StockRecord",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Товарная запись",
    )

    # PRODUCT INFORMATION
    # -------------------

    # We don't want any hard links between orders and the products table so we
    # allow this link to be NULLable.
    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Продукт",
    )
    title = models.CharField(("Название продукта", "Название"), max_length=255)
    # UPC can be null because it's usually set as the product's UPC, and that
    # can be null as well
    upc = models.CharField("Товарный код продукта UPC", max_length=128, blank=True, null=True)

    quantity = models.PositiveIntegerField("Количество", default=1)

    # REPORTING INFORMATION
    # ---------------------

    # Price information (these fields are actually redundant as the information
    # can be calculated from the LinePrice models
    line_price = models.DecimalField(
        "Цена", decimal_places=2, max_digits=12
    )

    # Price information before discounts are applied
    line_price_before_discounts = models.DecimalField(
        "Цена без учета скидок", decimal_places=2, max_digits=12
    )

    # Normal site price for item (without discounts)
    unit_price = models.DecimalField(
        "Цена за единицу товара",
        decimal_places=2,
        max_digits=12,
        blank=True,
        null=True,
    )

    tax_code = models.CharField(
        "Налоговый код", max_length=64, blank=True, null=True
    )

    # Partners often want to assign some status to each line to help with their
    # own business processes.
    status = models.CharField("Статус", max_length=255, blank=True)

    #: Order status pipeline.  This should be a dict where each (key, value)
    #: corresponds to a status and the possible statuses that can follow that
    #: one.
    pipeline = getattr(settings, "OSCAR_LINE_STATUS_PIPELINE", {})

    class Meta:
        abstract = True
        app_label = "order"
        # Enforce sorting in order of creation.
        ordering = ["pk"]
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        if self.product:
            title = self.product.title
        else:
            title = ("<Товар не найден>")
        return ("Товар '%(name)s', количество '%(qty)s'") % {
            "name": title,
            "qty": self.quantity,
        }

    @classmethod
    def all_statuses(cls):
        """
        Return all possible statuses for an order line
        """
        return list(cls.pipeline.keys())

    def available_statuses(self):
        """
        Return all possible statuses that this order line can move to
        """
        return self.pipeline.get(self.status, ())

    def set_status(self, new_status):
        """
        Set a new status for this line

        If the requested status is not valid, then ``InvalidLineStatus`` is
        raised.
        """
        if new_status == self.status:
            return

        old_status = self.status

        if new_status not in self.available_statuses():
            raise exceptions.InvalidLineStatus(
                (
                    "'%(new_status)s' недействительный статус (текущий статус:"
                    " '%(status)s')"
                )
                % {"new_status": new_status, "status": self.status}
            )
        self.status = new_status
        self.save()

        # Send signal for handling status changed
        order_line_status_changed.send(
            sender=self,
            line=self,
            old_status=old_status,
            new_status=new_status,
        )

    set_status.alters_data = True
    
    @property
    def options(self):
        ops = []
        d = ""
        for attribute in self.attributes.all():
            if attribute.option:
                value = attribute.value
                if isinstance(value, list):
                    ops.append(
                        "%s:  %s"
                        % (attribute.option.name, (", ".join([str(v) for v in value])))
                    )
                else:
                    ops.append("%s:  %s" % (attribute.option.name, value))
        if ops:
            d = "%s" % ("\n".join(ops))
        return d
    
    @property 
    def additions(self):
        addit = []
        d = ""
        for attribute in self.attributes.all():
            if attribute.additional:
                value = attribute.value
                if value > 0:
                    addit.append("%s (%s шт.)" % (attribute.additional.name, value))
            if addit:
                d = "%s" % (", ".join(addit))
        return d
    
    @property 
    def variants(self):
        slug = ""
        if self.product.variant:
            slug = self.product.variant

        return slug

    @property
    def discount(self):
        return self.line_price_before_discounts - self.line_price

    # Shipping status helpers

    @property
    def shipping_status(self):
        """
        Returns a string summary of the shipping status of this line
        """
        status_map = self.shipping_event_breakdown
        if not status_map:
            return ""

        events = []
        last_complete_event_name = None
        for event_dict in reversed(list(status_map.values())):
            if event_dict["quantity"] == self.quantity:
                events.append(event_dict["name"])
                last_complete_event_name = event_dict["name"]
            else:
                events.append(
                    "%s (%d/%d items)"
                    % (event_dict["name"], event_dict["quantity"], self.quantity)
                )

        if last_complete_event_name == list(status_map.values())[0]["name"]:
            return last_complete_event_name

        return ", ".join(events)

    def is_shipping_event_permitted(self, event_type, quantity):
        """
        Test whether a shipping event with the given quantity is permitted

        This method should normally be overridden to ensure that the
        prerequisite shipping events have been passed for this line.
        """
        # Note, this calculation is simplistic - normally, you will also need
        # to check if previous shipping events have occurred.  Eg, you can't
        # return lines until they have been shipped.
        current_qty = self.shipping_event_quantity(event_type)
        return (current_qty + quantity) <= self.quantity

    def shipping_event_quantity(self, event_type):
        """
        Return the quantity of this line that has been involved in a shipping
        event of the passed type.
        """
        result = self.shipping_event_quantities.filter(
            event__event_type=event_type
        ).aggregate(Sum("quantity"))
        if result["quantity__sum"] is None:
            return 0
        else:
            return result["quantity__sum"]

    def has_shipping_event_occurred(self, event_type, quantity=None):
        """
        Test whether this line has passed a given shipping event
        """
        if not quantity:
            quantity = self.quantity
        return self.shipping_event_quantity(event_type) == quantity

    def get_event_quantity(self, event):
        """
        Fetches the ShippingEventQuantity instance for this line

        Exists as a separate method so it can be overridden to avoid
        the DB query that's caused by get().
        """
        return event.line_quantities.get(line=self)

    @property
    def shipping_event_breakdown(self):
        """
        Returns a dict of shipping events that this line has been through
        """
        status_map = {}
        for event in self.shipping_events.all():
            event_type = event.event_type
            event_name = event_type.name
            event_quantity = self.get_event_quantity(event).quantity
            if event_name in status_map:
                status_map[event_name]["quantity"] += event_quantity
            else:
                status_map[event_name] = {
                    "event_type": event_type,
                    "name": event_name,
                    "quantity": event_quantity,
                }
        return status_map

    # Payment event helpers

    def is_payment_event_permitted(self, event_type, quantity):
        """
        Test whether a payment event with the given quantity is permitted.

        Allow each payment event type to occur only once per quantity.
        """
        current_qty = self.payment_event_quantity(event_type)
        return (current_qty + quantity) <= self.quantity

    def payment_event_quantity(self, event_type):
        """
        Return the quantity of this line that has been involved in a payment
        event of the passed type.
        """
        result = self.payment_event_quantities.filter(
            event__event_type=event_type
        ).aggregate(Sum("quantity"))
        if result["quantity__sum"] is None:
            return 0
        else:
            return result["quantity__sum"]

    @property
    def is_product_deleted(self):
        return self.product is None

    def is_available_to_reorder(self, basket, strategy):
        """
        Test if this line can be re-ordered using the passed strategy and
        basket
        """
        
        if not self.product:
            return False, (
                ("'%(title)s' больше недоступно") % {"title": self.title}
            )

        try:
            # переделай. если несолько продуктов с разными параметрами но один продукт типа товар2, то он добавит каждого по 1 если доступен всего 1, получается всего будет 2, изза этого ощиьки в форме
            basket_line = basket.lines.get(product_id=self.product.id)
        except basket.lines.model.DoesNotExist:
            desired_qty = self.quantity
        else:
            desired_qty = basket_line.quantity + self.quantity

        result = strategy.fetch_for_product(self.product)
        is_available, reason = result.availability.is_purchase_permitted(
            quantity=desired_qty
        )
        if not is_available:
            return False, reason
        return True, None


class AbstractLineAttribute(models.Model):
    """
    An attribute of a line
    """

    line = models.ForeignKey(
        "order.Line",
        on_delete=models.CASCADE,
        related_name="attributes",
        verbose_name="Позиция",
    )
    option = models.ForeignKey(
        "catalogue.Option",
        null=True,
        on_delete=models.SET_NULL,
        related_name="line_attributes",
        verbose_name="Опция",
    )
    additional = models.ForeignKey(
        "catalogue.Additional",
        null=True,
        on_delete=models.SET_NULL,
        related_name="line_additionals",
        verbose_name="Доп. товар",
    )

    type = models.CharField("Тип", max_length=128)
    value = models.JSONField("Значение", encoder=DjangoJSONEncoder)

    class Meta:
        abstract = True
        app_label = "order"
        verbose_name = "Атрибут позиции"
        verbose_name_plural = "Атрибуты позиций"

    def __str__(self):
        return "%s = %s" % (self.type, self.value)


class AbstractLinePrice(models.Model):
    """
    For tracking the prices paid for each unit within a line.

    This is necessary as offers can lead to units within a line
    having different prices.  For example, one product may be sold at
    50% off as it's part of an offer while the remainder are full price.
    """

    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="line_prices",
        verbose_name="Опция",
    )
    line = models.ForeignKey(
        "order.Line",
        on_delete=models.CASCADE,
        related_name="prices",
        verbose_name="Позиция",
    )
    quantity = models.PositiveIntegerField("Количество", default=1)
    price = models.DecimalField(
        "Цена", decimal_places=2, max_digits=12
    )
    shipping = models.DecimalField(
        "Доставка", decimal_places=2, max_digits=12, default=0
    )
    tax_code = models.CharField(
        "Налоговый код", max_length=64, blank=True, null=True
    )

    class Meta:
        abstract = True
        app_label = "order"
        ordering = ("id",)
        verbose_name = "Цена позиции"
        verbose_name_plural = "Цены позиций"

    def __str__(self):
        return ("Позиция '%(number)s' (количество %(qty)d) цена %(price)s") % {
            "number": self.line,
            "qty": self.quantity,
            "price": self.price,
        }


# PAYMENT EVENTS


class AbstractPaymentEventType(models.Model):
    """
    Payment event types are things like 'Paid', 'Failed', 'Refunded'.

    These are effectively the transaction types.
    """

    name = models.CharField("Имя", max_length=128, unique=True)
    code = AutoSlugField("Код", max_length=128, unique=True, populate_from="name")

    class Meta:
        abstract = True
        app_label = "order"
        verbose_name = "Тип платежного события"
        verbose_name_plural = "Типы платежных событий"
        ordering = ("name",)

    def __str__(self):
        return self.name


class AbstractPaymentEvent(models.Model):
    """
    A payment event for an order

    For example:

    * All lines have been paid for
    * 2 lines have been refunded
    """

    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="payment_events",
        verbose_name="Заказ",
    )
    amount = models.DecimalField("Сумма", decimal_places=2, max_digits=12)
    # The reference should refer to the transaction ID of the payment gateway
    # that was used for this event.
    reference = models.CharField("Референс", max_length=128, blank=True)
    lines = models.ManyToManyField(
        "order.Line", through="PaymentEventQuantity", verbose_name="Позиции"
    )
    event_type = models.ForeignKey(
        "order.PaymentEventType", on_delete=models.CASCADE, verbose_name="Тип события"
    )
    # Allow payment events to be linked to shipping events.  Often a shipping
    # event will trigger a payment event and so we can use this FK to capture
    # the relationship.
    shipping_event = models.ForeignKey(
        "order.ShippingEvent",
        null=True,
        on_delete=models.CASCADE,
        related_name="payment_events",
    )
    date_created = models.DateTimeField(
        "Дата создания", auto_now_add=True, db_index=True
    )

    class Meta:
        abstract = True
        app_label = "order"
        verbose_name = "Платежное событие"
        verbose_name_plural = "Платежные события"
        ordering = ["-date_created"]

    def __str__(self):
        return "Платежное событие %s" % self.order

    def num_affected_lines(self):
        return self.lines.all().count()


class PaymentEventQuantity(models.Model):
    """
    A "through" model linking lines to payment events
    """

    event = models.ForeignKey(
        "order.PaymentEvent",
        on_delete=models.CASCADE,
        related_name="line_quantities",
        verbose_name="Событие",
    )
    line = models.ForeignKey(
        "order.Line",
        on_delete=models.CASCADE,
        related_name="payment_event_quantities",
        verbose_name="Позиция",
    )
    quantity = models.PositiveIntegerField("Количество")

    class Meta:
        app_label = "order"
        verbose_name = "Событие платежа - Количество"
        verbose_name_plural = "События платежей - Количества"
        unique_together = ("event", "line")


# SHIPPING EVENTS


class AbstractShippingEvent(models.Model):
    """
    An event is something which happens to a group of lines such as
    1 item being dispatched.
    """

    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="shipping_events",
        verbose_name="Заказ",
    )
    lines = models.ManyToManyField(
        "order.Line",
        related_name="shipping_events",
        through="ShippingEventQuantity",
        verbose_name="Позиции",
    )
    event_type = models.ForeignKey(
        "order.ShippingEventType",
        on_delete=models.CASCADE,
        verbose_name="Тип события",
    )
    notes = models.TextField(
        "Заметка события",
        blank=True,
        help_text="Это может быть номер отправки или номер отслеживания.",
    )
    date_created = models.DateTimeField(
        "Дата создания", auto_now_add=True, db_index=True
    )

    class Meta:
        abstract = True
        app_label = "order"
        verbose_name = "Событие доставки"
        verbose_name_plural = "События доставки"
        ordering = ["-date_created"]

    def __str__(self):
        return "Заказ #%(number)s, тип %(type)s" % {
            "number": self.order.number,
            "type": self.event_type,
        }

    def num_affected_lines(self):
        return self.lines.count()


class ShippingEventQuantity(models.Model):
    """
    A "through" model linking lines to shipping events.

    This exists to track the quantity of a line that is involved in a
    particular shipping event.
    """

    event = models.ForeignKey(
        "order.ShippingEvent",
        on_delete=models.CASCADE,
        related_name="line_quantities",
        verbose_name="Событие",
    )
    line = models.ForeignKey(
        "order.Line",
        on_delete=models.CASCADE,
        related_name="shipping_event_quantities",
        verbose_name="Позиция",
    )
    quantity = models.PositiveIntegerField("Количество")

    class Meta:
        app_label = "order"
        verbose_name = "Событие доставки - Количество"
        verbose_name_plural = "События доставок - Количества"
        unique_together = ("event", "line")

    def save(self, *args, **kwargs):
        # Default quantity to full quantity of line
        if not self.quantity:
            self.quantity = self.line.quantity
        # Ensure we don't violate quantities constraint
        if not self.line.is_shipping_event_permitted(
            self.event.event_type, self.quantity
        ):
            raise exceptions.InvalidShippingEvent
        super().save(*args, **kwargs)

    def __str__(self):
        return ("%(product)s - количество %(qty)d") % {
            "product": self.line.product,
            "qty": self.quantity,
        }


class AbstractShippingEventType(models.Model):
    """
    A type of shipping/fulfilment event

    E.g.: 'Shipped', 'Cancelled', 'Returned'
    """

    # Name is the friendly description of an event
    name = models.CharField("Имя", max_length=255, unique=True)
    # Code is used in forms
    code = AutoSlugField("Код", max_length=128, unique=True, populate_from="name")

    class Meta:
        abstract = True
        app_label = "order"
        verbose_name = "Тип события доставки"
        verbose_name_plural = "Типы событий доставки"
        ordering = ("name",)

    def __str__(self):
        return self.name

    

# DISCOUNTS
class AbstractOrderDiscount(models.Model):
    """
    A discount against an order.

    Normally only used for display purposes so an order can be listed with
    discounts displayed separately even though in reality, the discounts are
    applied at the line level.

    This has evolved to be a slightly misleading class name as this really
    track benefit applications which aren't necessarily discounts.
    """

    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="discounts",
        verbose_name="Заказ",
    )

    # We need to distinguish between basket discounts, shipping discounts and
    # 'deferred' discounts.
    BASKET, SHIPPING, DEFERRED = "Корзина", "Доставка", "Отложенная"
    CATEGORY_CHOICES = (
        (BASKET, "Скидка на элементы корзины"),
        (SHIPPING, "Скидка на доставку"),
        (DEFERRED, "Отложенная скидка"),
    )
    category = models.CharField(
        "Категория скидки", default=BASKET, max_length=64, choices=CATEGORY_CHOICES
    )

    offer_id = models.PositiveIntegerField("ID Предложения", blank=True, null=True)
    offer_name = models.CharField(
        "Название предложения", max_length=128, db_index=True, blank=True
    )
    voucher_id = models.PositiveIntegerField("D Промокода", blank=True, null=True)
    voucher_code = models.CharField(
        "Код", max_length=128, db_index=True, blank=True
    )
    frequency = models.PositiveIntegerField("Частота", null=True)
    amount = models.DecimalField(
        "Сумма", decimal_places=2, max_digits=12, default=0
    )

    # Post-order offer applications can return a message to indicate what
    # action was taken after the order was placed.
    message = models.TextField(blank=True)

    @property
    def is_basket_discount(self):
        return self.category == self.BASKET

    @property
    def is_shipping_discount(self):
        return self.category == self.SHIPPING

    @property
    def is_post_order_action(self):
        return self.category == self.DEFERRED

    class Meta:
        abstract = True
        app_label = "order"
        ordering = ["pk"]
        verbose_name = "Скидка в заказе"
        verbose_name_plural = "Скидки в заказах"

    def save(self, *args, **kwargs):
        if self.offer_id and not self.offer_name:
            offer = self.offer
            if offer:
                self.offer_name = offer.name

        if self.voucher_id and not self.voucher_code:
            voucher = self.voucher
            if voucher:
                self.voucher_code = voucher.code

        super().save(**kwargs)

    def __str__(self):
        return "Скидка %(amount)r заказа %(order)s" % {
            "amount": self.amount,
            "order": self.order,
        }

    @property
    def offer(self):
        Offer = get_model("offer", "ConditionalOffer")
        try:
            return Offer.objects.get(id=self.offer_id)
        except Offer.DoesNotExist:
            return None

    @property
    def voucher(self):
        Voucher = get_model("voucher", "Voucher")
        try:
            return Voucher.objects.get(id=self.voucher_id)
        except Voucher.DoesNotExist:
            return None

    def description(self):
        if self.voucher_code:
            return self.voucher_code
        return self.offer_name or ""
    


class AbstractOrderLineDiscount(models.Model):
    line = models.ForeignKey(
        "order.Line",
        on_delete=models.CASCADE,
        related_name="discounts",
        verbose_name="Позиция",
    )
    order_discount = models.ForeignKey(
        "order.OrderDiscount",
        on_delete=models.CASCADE,
        related_name="discount_lines",
        verbose_name="Скидка заказа",
    )

    amount = models.DecimalField(
        "Скидка позиции", decimal_places=2, max_digits=12, default=0
    )

    class Meta:
        abstract = True
        app_label = "order"
        ordering = ["pk"]
        verbose_name = "Скидка позиции заказа"
        verbose_name_plural = "Скидки позиций заказов"


class AbstractSurcharge(models.Model):
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="surcharges",
        verbose_name="Дополнительные сборы",
    )

    name = models.CharField("Название дополнительного сбора", max_length=128)

    code = models.CharField("Код дополнительных сборов", max_length=128)

    money = models.DecimalField(
        "Сумма дополнительных сборов", decimal_places=2, max_digits=12, default=0
    )
    tax_code = models.CharField(
        "Налоговый код", max_length=64, blank=True, null=True
    )

    class Meta:
        abstract = True
        app_label = "order"
        ordering = ["pk"]
        verbose_name = "Дополнительный сбор"
        verbose_name_plural = "Дополнительные сборы"
