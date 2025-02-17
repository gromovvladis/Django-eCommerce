import datetime

from django.db import models, router
from django.db.models import F, signals, Value
from django.db.models.functions import Coalesce, Least
from django.utils.functional import cached_property
from django.utils import timezone

from oscar.apps.store.exceptions import InvalidStockAdjustment
from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.utils import get_default_currency
from oscar.models.fields import AutoSlugField


class Store(models.Model):
    """
    A fulfilment store. An individual or company who can fulfil products.
    E.g. for physical goods, somebody with a warehouse and means of delivery.

    Creating one or more instances of the Store model is a required step in
    setting up an Oscar deployment. Many Oscar deployments will only have one
    fulfilment store.
    """

    code = AutoSlugField(
        "Код", max_length=128, unique=True, db_index=True, populate_from="name"
    )
    name = models.CharField(
        "Название",
        max_length=128,
        blank=True,
        db_index=True,
    )
    evotor_id = models.CharField(
        "ID Эвотор",
        max_length=128,
        blank=True,
        null=True,
        db_index=True,
    )
    #: A store can have users assigned to it. This is used
    #: for access modelling in the permission-based dashboard
    users = models.ManyToManyField(
        AUTH_USER_MODEL,
        related_name="stores",
        blank=True,
        verbose_name="Персонал",
        db_index=True,
    )
    start_worktime = models.TimeField(
        "Время начала смены", default=datetime.time(10, 0)
    )
    end_worktime = models.TimeField(
        "Время окончания смены", default=datetime.time(22, 0)
    )
    terminals = models.ManyToManyField(
        "store.Terminal", related_name="stores", verbose_name="Терминал", blank=True
    )
    is_active = models.BooleanField(
        "Активен",
        default=True,
        db_index=True,
        help_text="Магазин доступен для клиентов?",
    )
    date_created = models.DateTimeField(
        "Дата создания", auto_now_add=True, db_index=True
    )
    date_updated = models.DateTimeField("Дата изменения", auto_now=True, db_index=True)

    @property
    def display_name(self):
        return self.name or self.code

    @cached_property
    def work_time(self):
        return f"{self.start_worktime.strftime('%H:%M')}-{self.end_worktime.strftime('%H:%M')}"

    @cached_property
    def primary_address(self):
        """
        Returns a stores primary address. Usually that will be the
        headquarters or similar.

        This is a rudimentary implementation that raises an error if there's
        more than one address. If you actually want to support multiple
        addresses, you will likely need to extend StoreAddress to have some
        field or flag to base your decision on.
        """
        address = self.address
        if not address:
            return ""
        else:
            return address

    # pylint: disable=unused-argument
    def get_address_for_stockrecord(self, stockrecord):
        """
        Stock might be coming from different warehouses. Overriding this
        function allows selecting the correct StoreAddress for the record.
        That can be useful when determining tax.
        """
        return self.primary_address

    class Meta:
        app_label = "store"
        ordering = ("name", "code")
        verbose_name = "Магазин"
        verbose_name_plural = "Магазины"

    def __str__(self):
        return self.display_name


class Terminal(models.Model):
    """
    Терминал из магазина Эвотор
    """

    name = models.CharField(
        "Название",
        max_length=128,
        blank=True,
    )
    evotor_id = models.CharField(
        "ID Эвотор",
        max_length=128,
        blank=True,
    )
    model = models.CharField("Модель терминала", max_length=128, blank=True, null=True)
    imei = models.CharField(
        "Код imei", max_length=128, unique=True, blank=True, null=True
    )
    serial_number = models.CharField(
        "Серийный номер",
        max_length=128,
        unique=True,
    )

    coords_long = models.CharField(
        "Координаты долгота", max_length=255, blank=True, null=True
    )
    coords_lat = models.CharField(
        "Координаты широта", max_length=255, blank=True, null=True
    )

    date_created = models.DateTimeField(
        "Дата создания", auto_now_add=True, db_index=True
    )
    date_updated = models.DateTimeField("Дата изменения", auto_now=True, db_index=True)

    @property
    def display_name(self):
        return self.name

    class Meta:
        app_label = "store"
        ordering = ("name", "serial_number")
        verbose_name = "Смарт терминал Эвотор"
        verbose_name_plural = "Смарт терминалы Эвотор"

    def __str__(self):
        return self.display_name


class BarCode(models.Model):

    code = models.CharField(
        "Штрих-код",
        max_length=128,
        unique=True,
    )

    class Meta:
        app_label = "store"
        ordering = ("code",)
        verbose_name = "Штрих-код"
        verbose_name_plural = "Штрих-коды"


class StockRecord(models.Model):
    """
    A stock record.

    This records information about a product from a fulfilment store, such as
    their SKU, the number they have in stock and price information.

    Stockrecords are used by 'strategies' to determine availability and pricing
    information for the customer.
    """

    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        verbose_name="Товар",
        related_name="stockrecords",
    )
    store = models.ForeignKey(
        "store.Store",
        on_delete=models.CASCADE,
        verbose_name="Магазин",
        related_name="stockrecords",
    )

    #: The fulfilment store will often have their own SKU for a product,
    #: which we store here.  This will sometimes be the same the product's article
    #: but not always.  It should be unique per store.
    #: See also http://en.wikipedia.org/wiki/Stock-keeping_unit
    evotor_code = models.CharField(
        "Эвотор Code",
        max_length=25,
        blank=True,
        help_text="Эвотор код, для связи товара и товарной записи",
    )

    # Price info:
    price_currency = models.CharField(
        "Валюта",
        max_length=12,
        default=get_default_currency,
        help_text="Валюта. Рубли = RUB",
    )

    bar_codes = models.ManyToManyField(
        "store.BarCode", related_name="bars", verbose_name="Штрих-коды", blank=True
    )

    # This is the base price for calculations - whether this is inclusive or exclusive of
    # tax depends on your implementation, as this is highly domain-specific.
    # It is nullable because some items don't have a fixed
    # price but require a runtime calculation (possibly from an external service).
    price = models.DecimalField(
        "Цена",
        decimal_places=2,
        max_digits=12,
        blank=True,
        null=True,
        help_text="Цена продажи",
    )
    old_price = models.DecimalField(
        "Цена до скидки",
        decimal_places=2,
        max_digits=12,
        blank=True,
        null=True,
        help_text="Цена до скидки. Оставить пустым, если скидки нет",
    )
    cost_price = models.DecimalField(
        "Цена закупки",
        decimal_places=2,
        max_digits=12,
        blank=True,
        null=True,
        help_text="Цена закупки товара",
    )
    NO_VAT, VAT_10, VAT_18, VAT_0, VAT_18_118, VAT_10_110 = (
        "NO_VAT",
        "VAT_10",
        "VAT_18",
        "VAT_0",
        "VAT_18_118",
        "VAT_10_110",
    )
    VAT_CHOICES = (
        (NO_VAT, "Без НДС."),
        (VAT_0, "Основная ставка 0%"),
        (VAT_10, "Основная ставка 10%."),
        (VAT_10_110, "Расчётная ставка 10%."),
        (
            VAT_18,
            "Основная ставка 18%. С первого января 2019 года может указывать как на 18%, так и на 20% ставку.",
        ),
        (
            VAT_18_118,
            "Расчётная ставка 18%. С первого января 2019 года может указывать как на 18%, так и на 20% ставку.",
        ),
    )
    tax = models.CharField(
        "Налог в процентах", default=NO_VAT, choices=VAT_CHOICES, max_length=128
    )

    #: Number of items in stock
    num_in_stock = models.PositiveIntegerField(
        "Количество в наличии",
        default=0,
        blank=True,
        null=True,
        help_text="В наличии",
    )

    #: The amount of stock allocated to orders but not fed back to the master
    #: stock system.  A typical stock update process will set the
    #: :py:attr:`.num_in_stock` variable to a new value and reset
    #: :py:attr:`.num_allocated` to zero.
    num_allocated = models.IntegerField(
        "Количество заказано",
        blank=True,
        null=True,
        help_text="Заказано",
    )

    #: Threshold for low-stock alerts.  When stock goes beneath this threshold,
    #: an alert is triggered so warehouse managers can order more.
    low_stock_threshold = models.PositiveIntegerField(
        "Граница малых запасов",
        blank=True,
        null=True,
        help_text="Граница малых запасов",
    )

    is_public = models.BooleanField(
        "Доступен",
        default=True,
        db_index=True,
        help_text="Товар доступен к покупке",
    )

    # Date information
    date_created = models.DateTimeField("Дата создания", auto_now_add=True)
    date_updated = models.DateTimeField("Дата изменения", auto_now=True, db_index=True)

    def __str__(self):
        msg = "Магазин: %s, товар: %s" % (
            self.store.display_name,
            self.product,
        )
        if self.evotor_code:
            msg = "%s (%s)" % (msg, self.evotor_code)
        return msg

    class Meta:
        app_label = "store"
        unique_together = ("store", "product")
        get_latest_by = "date_updated"
        verbose_name = "Товарная запись"
        verbose_name_plural = "Товарные записи"

    @property
    def net_stock_level(self):
        """
        The effective number in stock (e.g. available to buy).

        This is correct property to show the customer, not the
        :py:attr:`.num_in_stock` field as that doesn't account for allocations.
        This can be negative in some unusual circumstances
        """
        if self.num_in_stock is None:
            return 0
        if self.num_allocated is None:
            return self.num_in_stock
        return self.num_in_stock - self.num_allocated

    @cached_property
    def can_track_allocations(self):
        """Return True if the Product is set for stock tracking."""
        return self.product.get_product_class().track_stock

    # 2-stage stock management model

    def allocate(self, quantity):
        """
        Record a stock allocation.

        This normally happens when a product is bought at checkout.  When the
        product is actually shipped, then we 'consume' the allocation.

        """
        # Doesn't make sense to allocate if stock tracking is off.
        if not self.can_track_allocations:
            return

        # Send the pre-save signal
        self.pre_save_signal()

        # Atomic update
        (
            self.__class__.objects.filter(pk=self.pk).update(
                num_allocated=(Coalesce(F("num_allocated"), 0) + quantity)
            )
        )

        # Make sure the current object is up-to-date
        self.refresh_from_db(fields=["num_allocated"])

        # Send the post-save signal
        self.post_save_signal()

    allocate.alters_data = True

    def is_allocation_consumption_possible(self, quantity):
        """
        Test if a proposed stock consumption is permitted
        """
        return quantity <= min(self.num_allocated, self.num_in_stock)

    def consume_allocation(self, quantity):
        """
        Consume a previous allocation

        This is used when an item is shipped.  We remove the original
        allocation and adjust the number in stock accordingly
        """
        if not self.can_track_allocations:
            return
        if not self.is_allocation_consumption_possible(quantity):
            raise InvalidStockAdjustment("Неверный запрос товарного запаса")

        # send the pre save signal
        self.pre_save_signal()

        # Atomically consume allocations and stock
        (
            self.__class__.objects.filter(pk=self.pk).update(
                num_allocated=(Coalesce(F("num_allocated"), 0) - quantity),
                num_in_stock=(Coalesce(F("num_in_stock"), 0) - quantity),
            )
        )

        # Make sure current object is up-to-date
        self.refresh_from_db(fields=["num_allocated", "num_in_stock"])

        # Send the post-save signal
        self.post_save_signal()

    consume_allocation.alters_data = True

    def cancel_allocation(self, quantity):
        if not self.can_track_allocations:
            return

        # send the pre save signal
        self.pre_save_signal()

        # Atomically consume allocations
        (
            self.__class__.objects.filter(pk=self.pk).update(
                num_allocated=Coalesce(F("num_allocated"), 0)
                - Least(Coalesce(F("num_allocated"), 0), quantity),
            )
        )

        # Make sure current object is up-to-date
        self.refresh_from_db(fields=["num_allocated"])

        # Send the post-save signal
        self.post_save_signal()

    cancel_allocation.alters_data = True

    def pre_save_signal(self):
        signals.pre_save.send(
            sender=self.__class__,
            instance=self,
            created=False,
            raw=False,
            using=router.db_for_write(self.__class__, instance=self),
        )

    def post_save_signal(self):
        signals.post_save.send(
            sender=self.__class__,
            instance=self,
            created=False,
            raw=False,
            using=router.db_for_write(self.__class__, instance=self),
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.evotor_code:
            self.evotor_code = self._generate_unique_evotor_code()
            self.save()

    def _generate_unique_evotor_code(self):
        prefix = "site"
        return f"{prefix}-{self.id}"

    @property
    def is_below_threshold(self):
        if self.low_stock_threshold is None:
            return False
        return self.net_stock_level < self.low_stock_threshold


class StockRecordOperation(models.Model):
    evotor_id = models.CharField(
        "ID Эвотор",
        max_length=128,
        blank=True,
        null=True,
    )
    stockrecord = models.ForeignKey(
        "store.StockRecord",
        on_delete=models.CASCADE,
        verbose_name="Товарная запись",
        related_name="operations",
    )
    ACCEPT, WRITE_OFF, INVENTORY = (
        "Приемка",
        "Списание",
        "Инвентаризация",
    )
    TYPE_CHOICES = (
        (ACCEPT, "Приемка"),
        (WRITE_OFF, "Списание"),
        (INVENTORY, "Инвентаризация"),
    )
    type = models.CharField(
        "Тип операции", default=ACCEPT, choices=TYPE_CHOICES, max_length=128
    )
    message = models.CharField(
        "Сообщение",
        blank=True,
        null=True,
        max_length=255,
        help_text="Комментарий к операции",
    )
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name="stockrecord_operations",
        verbose_name="Сотрудник",
        db_index=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    num = models.IntegerField(
        "Количество",
        blank=False,
        null=False,
        help_text="Количество товара",
    )

    # Date information
    date_created = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return "Товарная запись: %s, Операция: %s, Количество: %s" % (
            self.stockrecord,
            self.type,
            self.num,
        )

    class Meta:
        app_label = "store"
        verbose_name = "Изменение товарной записи"
        verbose_name_plural = "Изменение товарных записей"

    def save(self, *args, **kwargs):
        self.create_operation()
        super().save(*args, **kwargs)

    def create_operation(self):
        operation_methods = {
            self.ACCEPT: self.accept,
            self.WRITE_OFF: self.write_off,
            self.INVENTORY: self.inventory,
        }
        operation_method = operation_methods.get(self.type)
        if operation_method:
            return operation_method()

    def accept(self):
        return self._update_stock(abs(self.num))

    def write_off(self):
        """Списание с учетом доступного количества"""
        if self.num > self.stockrecord.net_stock_level:
            raise ValueError(
                f"Нельзя списать больше, чем доступно с учетом заказаных товаров. Доступно {self.stockrecord.net_stock_level}"
            )

        return self._update_stock(-abs(self.num))

    def inventory(self):
        """Обновляет `num_in_stock` и фиксирует разницу в `num`"""
        old_num = self.stockrecord.num_in_stock or 0
        self.stockrecord.num_in_stock = abs(self.num)
        self.stockrecord.save(update_fields=["num_in_stock"])
        self.num = self.num - old_num
        return self.stockrecord.num_in_stock

    def _update_stock(self, delta):
        """Обновление остатков на складе"""
        old_num = self.stockrecord.num_in_stock or 0
        self.stockrecord.num_in_stock = old_num + delta
        self.stockrecord.save(update_fields=["num_in_stock"])
        return self.stockrecord.num_in_stock


class StockAlert(models.Model):
    """
    A stock alert. E.g. used to notify users when a product is 'back in stock'.
    """

    stockrecord = models.ForeignKey(
        "store.StockRecord",
        on_delete=models.CASCADE,
        related_name="alerts",
        verbose_name="Товарная запись",
    )

    OPEN, CLOSED = "Открыто", "Закрыто"

    status_choices = (
        (OPEN, "Открыто"),
        (CLOSED, "Закрыто"),
    )
    status = models.CharField(
        "Статус", max_length=128, default=OPEN, choices=status_choices
    )
    date_created = models.DateTimeField(
        "Дата создания", auto_now_add=True, db_index=True
    )
    date_closed = models.DateTimeField("Дата закрытия", blank=True, null=True)

    def close(self):
        self.status = self.CLOSED
        self.date_closed = timezone.now()
        self.save()

    close.alters_data = True

    def __str__(self):
        return '<Уведомление о наличии товара "%(stock)s" со статусом %(status)s>' % {
            "stock": self.stockrecord,
            "status": self.status,
        }

    class Meta:
        app_label = "store"
        ordering = ("-date_created",)
        verbose_name = "Уведомление товарного запаса"
        verbose_name_plural = "Уведомления товарных запасов"


class StoreCash(models.Model):
    store = models.OneToOneField(
        "store.Store",
        on_delete=models.CASCADE,
        verbose_name="Магазин",
        related_name="cash",
    )
    sum = models.IntegerField(
        "Наличные",
        blank=False,
        null=False,
        default=0,
        help_text="Сумма наличных в магазине",
    )
    date_updated = models.DateTimeField("Дата изменения", auto_now=True)

    def __str__(self):
        return "Магазин: %s, Наличные: %s" % (
            self.store,
            self.sum,
        )

    class Meta:
        app_label = "store"
        verbose_name = "Наличные в магазине"
        verbose_name_plural = "Наличные в магазинах"


class StoreCashTransaction(models.Model):
    evotor_id = models.CharField(
        "ID Эвотор",
        max_length=128,
        blank=True,
        null=True,
    )
    store = models.ForeignKey(
        "store.Store",
        on_delete=models.CASCADE,
        verbose_name="Магазин",
        related_name="transactions",
    )
    order = models.ForeignKey(
        "order.Order",
        related_name="cash_transactions",
        null=True,
        on_delete=models.SET_NULL,
    )
    CASH_INCOME, CASH_OUTCOME, PAYMENT, REFUND = (
        "Внесение наличных",
        "Изъятие наличных",
        "Оплата заказа",
        "Возврат заказа",
    )
    TYPE_CHOICES = (
        (CASH_INCOME, "Внесение наличных"),
        (CASH_OUTCOME, "Изъятие наличных"),
        (PAYMENT, "Оплата заказа"),
        (REFUND, "Возврат заказа"),
    )
    type = models.CharField(
        "Тип операции", default=CASH_INCOME, choices=TYPE_CHOICES, max_length=128
    )
    description = models.CharField(
        "Сообщение",
        blank=True,
        null=True,
        max_length=255,
        help_text="Комментарий к операции",
    )
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name="cash_transactions",
        verbose_name="Сотрудник",
        db_index=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    sum = models.IntegerField(
        "Наличные",
        blank=False,
        null=False,
        help_text="Сумма наличных в магазине",
    )
    date_created = models.DateTimeField(
        "Дата создания", auto_now_add=True, db_index=True
    )

    def __str__(self):
        return "Транзакция %s, Магазин: %s, Сумма: %s" % (
            self.type,
            self.store,
            self.sum,
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.create_transaction()

    class Meta:
        app_label = "store"
        verbose_name = "Внесение / Изъятие наличных"
        verbose_name_plural = "Внесения и изъятия наличных"

    def create_transaction(self):
        cash, _ = StoreCash.objects.get_or_create(store=self.store)
        cash.sum += (
            self.sum if self.type in [self.CASH_INCOME, self.PAYMENT] else -self.sum
        )
        cash.save()
        return cash.sum
