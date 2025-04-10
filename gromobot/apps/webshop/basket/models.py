import re
import zlib
from decimal import Decimal as D
from operator import itemgetter

from core.compat import AUTH_USER_MODEL
from core.loading import get_class, get_model
from core.models.fields import SlugField
from core.utils import get_default_currency
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Exists, OuterRef, Q, Sum
from django.utils.encoding import smart_str
from django.utils.functional import cached_property
from django.utils.timezone import now

OfferApplications = get_class("webshop.offer.results", "OfferApplications")
Unavailable = get_class("webshop.store.availability", "Unavailable")
StockRequired = get_class("webshop.store.availability", "StockRequired")
LineDiscountRegistry = get_class("webshop.basket.utils", "LineDiscountRegistry")
OpenBasketManager = get_class("webshop.basket.managers", "OpenBasketManager")

Store = get_model("store", "Store")
StockRecord = get_model("store", "StockRecord")


class Basket(models.Model):
    """
    Basket object
    """

    # Baskets can be anonymously owned - hence this field is nullable.  When a
    # anon user signs in, their two baskets are merged.
    owner = models.ForeignKey(
        AUTH_USER_MODEL,
        null=True,
        db_index=True,
        related_name="baskets",
        on_delete=models.CASCADE,
        verbose_name="Владелец",
    )

    store = models.ForeignKey(
        "store.Store",
        related_name="baskets",
        null=True,
        db_index=True,
        blank=False,
        verbose_name="Магазин",
        on_delete=models.SET_NULL,
    )

    # Basket statuses
    # - Frozen is for when a basket is in the process of being submitted
    #   and we need to prevent any changes to it.
    OPEN, MERGED, FROZEN, SUBMITTED = (
        "Open",
        "Merged",
        "Frozen",
        "Submitted",
    )
    STATUS_CHOICES = (
        (OPEN, "Открыто - сейчас активна"),
        (MERGED, "Объединено – заменено другой корзиной"),
        (FROZEN, "Заморожено – корзину нельзя изменить"),
        (SUBMITTED, "Потдвержено - заказано"),
    )
    status = models.CharField(
        "Статус", max_length=128, default=OPEN, choices=STATUS_CHOICES
    )

    # A basket can have many vouchers attached to it.  However, it is common
    # for sites to only allow one voucher per basket - this will need to be
    # enforced in the project's codebase.
    vouchers = models.ManyToManyField(
        "voucher.Voucher", verbose_name="Промокод", blank=True
    )

    date_created = models.DateTimeField("Дата создания", auto_now_add=True)
    date_merged = models.DateTimeField("Дата объединения", null=True, blank=True)
    date_submitted = models.DateTimeField("Дата подтверждения", null=True, blank=True)

    # Only if a basket is in one of these statuses can it be edited
    editable_statuses = (OPEN,)

    class Meta:
        app_label = "basket"
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    objects = models.Manager()
    open = OpenBasketManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # We keep a cached copy of the basket lines as we refer to them often
        # within the same request cycle.  Also, applying offers will append
        # discount data to the basket lines which isn't persisted to the DB and
        # so we want to avoid reloading them as this would drop the discount
        # information.
        self._lines = None
        self._filtered_lines = None
        self.offer_applications = OfferApplications()

    def __str__(self):
        return "%(status)s Корзина (пользователь: %(owner)s)" % {
            "status": self.status,
            "owner": self.owner,
        }

    # ========
    # Strategy
    # ========

    @property
    def has_strategy(self):
        return hasattr(self, "_strategy")

    def _get_strategy(self):
        if not self.has_strategy:
            raise RuntimeError(
                "No strategy class has been assigned to this basket. "
                "This is normally assigned to the incoming request in "
                "apps.webshop.basket.middleware.BasketMiddleware. "
                "Since it is missing, you must be doing something different. "
                "Ensure that a strategy instance is assigned to the basket!"
            )
        return self._strategy

    def _set_strategy(self, strategy):
        self._strategy = strategy  # pylint: disable=W0201

    strategy = property(_get_strategy, _set_strategy)

    def _all_lines(self):
        """
        Return a cached set of basket lines.
        """
        if self.id is None:
            return self.lines.model.objects.none()  # pylint: disable=E1101
        if self._lines is None:
            self._lines = (
                self.lines.select_related("product", "stockrecord")
                .prefetch_related(
                    "attributes",
                    "product__images",
                    "product__categories",
                    "product__stockrecords",
                )
                .annotate(
                    has_stockrecord=Exists(
                        StockRecord.objects.filter(
                            product=OuterRef("product_id")
                        ).filter(Q(store_id=self.store_id) if self.store_id else Q())
                    )
                )
                .order_by(self._meta.pk.name)
            )
        return self._lines

    def all_lines(self):
        if self._filtered_lines is None:
            self._filtered_lines = [
                line for line in self._all_lines() if line.has_stockrecord
            ]
        return self._filtered_lines

    def max_allowed_quantity(self):
        """
        Returns maximum product quantity, that can be added to the basket
        with the respect to basket quantity threshold.
        """
        basket_threshold = settings.MAX_BASKET_QUANTITY_THRESHOLD
        if basket_threshold:
            total_basket_quantity = self.num_items
            max_allowed = basket_threshold - total_basket_quantity
            return max_allowed, basket_threshold
        return None, None

    def is_quantity_allowed(self, qty, line=None):
        """
        Test whether the passed quantity of items can be added to the basket
        """
        # We enforce a max threshold to prevent a DOS attack via the offers
        # system.
        max_allowed, basket_threshold = self.max_allowed_quantity()

        if line is not None:
            (
                line_purchase_permitted,
                reason,
            ) = line.purchase_info.availability.is_purchase_permitted(qty)

            if not line_purchase_permitted:
                return line_purchase_permitted, reason

            # Also check if it's permitted with potentional other lines of the same product & stockrecord
            total_lines_quantity = self.basket_quantity(line) + qty
            (
                line_purchase_permitted,
                reason,
            ) = line.purchase_info.availability.is_purchase_permitted(
                total_lines_quantity
            )

            if not line_purchase_permitted:
                return line_purchase_permitted, (
                    "Доступный запас составляет только %(max)d, "
                ) % {"max": line.purchase_info.availability.num_available}

        if max_allowed is not None and qty > max_allowed:
            return False, (
                "Из-за технических ограничений мы не можем оформить заказ на"
                " более чем %(threshold)d товаров в одном заказе."
            ) % {"threshold": basket_threshold}

        return True, None

    def basket_quantity(self, line):
        """Return the quantity of similar lines in the basket.
        The basket can contain multiple lines with the same product and
        stockrecord, but different options. Those quantities are summed up.
        """
        matching_lines = self.lines.filter(stockrecord_id=line.stockrecord_id)
        quantity = matching_lines.aggregate(Sum("quantity"))["quantity__sum"]
        return quantity or 0

    # ============
    # Manipulation
    # ============

    def flush(self):
        """
        Remove all lines from basket.
        """
        if self.status == self.FROZEN:
            raise PermissionDenied("A frozen basket cannot be flushed")
        self.lines.all().delete()
        self._lines = None
        self._filtered_lines = None

    # pylint: disable=unused-argument
    def get_stock_info(self, product, options, additionals):
        """
        Hook for implementing strategies that depend on product options
        """
        # The built-in strategies don't use options, so initially disregard
        # them.
        return self.strategy.fetch_for_product(product)

    def check_store(self, line):
        if not self.store_id or self.is_empty:
            self.store_id = line.stockrecord.store_id
            self.save()
        else:
            store = Store.objects.get(store_id=self.store_id)
            line_store = Store.objects.get(store_id=line.stockrecord.store_id)

            if line_store.store_id != self.store_id:
                raise ValueError(
                    f"Данный товар не доступен в {store.primary_address}, закажите его в {line_store.primary_address}"
                )

    def add_product(self, product, quantity=1, options=None, additionals=None):
        """
        Add a product to the basket

        The 'options' list should contains dicts with keys 'option' and 'value'
        which link the relevant product.Option model and string value
        respectively.

        Returns (line, created).
          line: the matching basket line
          created: whether the line was created or updated
        """
        line, created = self.get_line(product, quantity, options, additionals)

        if created:
            self.check_store(line)
            for option_dict in options:
                line.attributes.create(
                    option=option_dict["option"], value=option_dict["value"]
                )
            for additional_dict in additionals:
                line.attributes.create(
                    additional=additional_dict["additional"],
                    value=additional_dict["value"],
                )

        else:
            line.quantity = max(0, line.quantity + quantity)
            line.save()
        self.reset_offer_applications()

        # Returning the line is useful when overriding this method.
        return line, created

    add_product.alters_data = True
    add = add_product

    def remove_product(self, product, quantity=1, options=None):
        """
        Remove a product from the basket

        """
        line, created = self.get_line(product, quantity, options)

        if created:
            return
        else:
            line.quantity = max(0, line.quantity - quantity)
            line.save()
        self.reset_offer_applications()

        # Returning the line is useful when overriding this method.
        return line, created

    remove_product.alters_data = True
    add = remove_product

    def get_line(self, product, quantity=1, options=None, additionals=None):
        if options is None:
            options = []
        if additionals is None:
            additionals = []

        if not self.id:
            self.save()

        # Ensure that all lines are the same currency
        price_currency = self.currency
        stock_info = self.get_stock_info(product, options, additionals)

        if not stock_info.price.exists:
            raise ValueError("Strategy hasn't found a price for product %s" % product)

        if price_currency and stock_info.price.currency != price_currency:
            raise ValueError(
                (
                    "Basket lines must all have the same currency. Proposed "
                    "line has currency %s, while basket has currency %s"
                )
                % (stock_info.price.currency, price_currency)
            )

        if stock_info.stockrecord is None:
            raise ValueError(
                (
                    "Basket lines must all have stock records. Strategy hasn't "
                    "found any stock record for product %s"
                )
                % product
            )

        # Line reference is used to distinguish between variations of the same
        # product (eg T-shirts with different personalisations)
        line_ref = self._create_line_reference(
            product, stock_info.stockrecord, options, additionals
        )

        # Determine price to store (if one exists).  It is only stored for
        # audit and sometimes caching.
        defaults = {
            "quantity": quantity,
            "price_currency": stock_info.price.currency,
            "tax_code": stock_info.stockrecord.tax,
        }

        line, created = self.lines.get_or_create(
            line_reference=line_ref,
            product=product,
            stockrecord=stock_info.stockrecord,
            defaults=defaults,
        )

        return line, created

    def applied_offers(self):
        """
        Return a dict of offers successfully applied to the basket.

        This is used to compare offers before and after a basket change to see
        if there is a difference.
        """
        return self.offer_applications.offers

    def reset_offer_applications(self):
        """
        Remove any discounts so they get recalculated
        """
        self.offer_applications = OfferApplications()
        self._lines = None
        self._filtered_lines = None

    def merge_line(self, line, add_quantities=True):
        """
        For transferring a line from another basket to this one.

        This is used with the "Saved" basket functionality.
        """
        try:
            existing_line = self.lines.get(line_reference=line.line_reference)
        except ObjectDoesNotExist:
            # Line does not already exist - reassign its basket
            line.basket._lines = None
            line.basket = self
            line.save()
        else:
            # Line already exists - assume the max quantity is correct and
            # delete the old
            if add_quantities:
                existing_line.quantity += line.quantity
            else:
                existing_line.quantity = max(existing_line.quantity, line.quantity)
            existing_line.save()
            line.delete()
        finally:
            self._lines = None
            self._filtered_lines = None

    merge_line.alters_data = True

    def merge(self, basket, add_quantities=True):
        """
        Merges another basket with this one.

        :basket: The basket to merge into this one.
        :add_quantities: Whether to add line quantities when they are merged.
        """
        # Use basket.lines.all instead of all_lines as this function is called
        # before a strategy has been assigned.
        for line_to_merge in basket.lines.all():
            self.merge_line(line_to_merge, add_quantities)
        basket.status = self.MERGED
        basket.date_merged = now()
        basket._lines = None
        basket._filtered_lines = None
        basket.save()
        self.store_id = basket.store_id
        self.save()
        # Ensure all vouchers are moved to the new basket
        for voucher in basket.vouchers.all():
            basket.vouchers.remove(voucher)
            self.vouchers.add(voucher)

    merge.alters_data = True

    def freeze(self):
        """
        Freezes the basket so it cannot be modified.
        """
        self.status = self.FROZEN
        self.save()

    freeze.alters_data = True

    def thaw(self):
        """
        Unfreezes a basket so it can be modified again
        """
        self.status = self.OPEN
        self.save()

    thaw.alters_data = True

    def submit(self):
        """
        Mark this basket as submitted
        """
        self.status = self.SUBMITTED
        self.date_submitted = now()
        self.save()

    submit.alters_data = True

    # Kept for backwards compatibility
    set_as_submitted = submit

    def is_shipping_required(self):
        """
        Test whether the basket contains physical products that require
        shipping.
        """
        for line in self.all_lines():
            if line.product.is_shipping_required:
                return True
        return False

    def change_basket_store(self, new_store_id):
        self.store_id = new_store_id
        self.save()
        self._update_lines()

    # =======
    # Helpers
    # =======

    def _update_lines(self):
        for line in self.all_lines():
            new_stockrecord = line.product.stockrecords.filter(
                store_id=self.store_id
            ).first()
            if new_stockrecord is not None:
                line.stockrecord = new_stockrecord
                line.line_reference = self._update_stockrecord(
                    line.line_reference, new_stockrecord.id
                )
                line.save()

    def _update_stockrecord(self, s: str, new: str) -> str:
        return re.sub(r"^([^_]+)_([^_]+)", rf"\1_{new}", s)

    def _create_line_reference(self, product, stockrecord, options, additionals):
        """
        Returns a reference string for a line based on the item
        and its options.
        """
        base = f"{product.id}_{stockrecord.id}"

        if not options and not additionals:
            return base

        repr_list = []

        if options:
            repr_list.extend(
                [{"key": repr(option["option"]), "value": repr(option["value"])}]
                for option in options
            )

        if additionals:
            repr_list.extend(
                [
                    {
                        "key": repr(additional["additional"]),
                        "value": repr(additional["value"]),
                    }
                ]
                for additional in additionals
            )

        repr_list.sort(key=itemgetter("key"))

        return f"{base}_{zlib.crc32(repr(repr_list).encode('utf8'))}"

    def _get_total(self, model_property):
        """
        For executing a named method on each line of the basket
        and returning the total.
        """
        total = D("0.00")
        for line in self.all_lines():
            try:
                total += getattr(line, model_property)
            except ObjectDoesNotExist:
                # Handle situation where the product may have been deleted
                pass
            except TypeError:
                # Handle Unavailable products with no known price
                info = self.get_stock_info(line.product, line.options, line.additions)
                if info.availability.is_available_to_buy:
                    raise
        return total

    # ==========
    # Properties
    # ==========

    @property
    def has_valid_lines(self):
        """
        Test if this basket is empty
        """
        return self.id is not None and self.num_items > 0

    @property
    def is_empty(self):
        """
        Test if this basket is empty
        """
        return self.id is None or sum(line.quantity for line in self._all_lines()) == 0

    @property
    def total(self):
        """
        Return total line price incl discounts
        """
        return self._get_total("line_price_incl_discounts")

    @property
    def total_discount(self):
        return self._get_total("discount_value")

    @property
    def offer_discounts(self):
        """
        Return basket discounts from non-voucher sources.  Does not include
        shipping discounts.
        """
        return self.offer_applications.offer_discounts

    @property
    def voucher_discounts(self):
        """
        Return discounts from vouchers
        """
        return self.offer_applications.voucher_discounts

    @property
    def has_shipping_discounts(self):
        return len(self.shipping_discounts) > 0

    @property
    def shipping_discounts(self):
        """
        Return discounts from vouchers
        """
        return self.offer_applications.shipping_discounts

    @property
    def post_order_actions(self):
        """
        Return discounts from vouchers
        """
        return self.offer_applications.post_order_actions

    @property
    def grouped_voucher_discounts(self):
        """
        Return discounts from vouchers but grouped so that a voucher which
        links to multiple offers is aggregated into one object.
        """
        return self.offer_applications.grouped_voucher_discounts

    @property
    def total_excl_discounts(self):
        """
        Return total price excluding discounts
        """
        return self._get_total("line_price")

    @property
    def num_lines(self):
        """Return number of lines"""
        return len(self.all_lines())

    @property
    def num_all_items(self):
        """Return number of items"""
        return sum(line.quantity for line in self._all_lines())

    @property
    def num_items(self):
        """Return number of items"""
        return sum(line.quantity for line in self.all_lines())

    @property
    def num_items_without_discount(self):
        return sum(line.quantity_without_discount for line in self.all_lines())

    @property
    def num_items_with_discount(self):
        return sum(line.quantity_with_discount for line in self.all_lines())

    @property
    def time_before_submit(self):
        if not self.date_submitted:
            return "Не отправлено"

        delta = self.date_submitted - self.date_created
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days} дней, {hours} часов, {minutes} минут"
        elif hours > 0:
            return f"{hours} часов, {minutes} минут"
        elif minutes > 0:
            return f"{minutes} минут, {seconds} секунд"
        else:
            return f"{seconds} секунд"

        # if not self.date_submitted:
        #     return None
        # return self.date_submitted - self.date_created

    @property
    def time_since_creation(self, test_datetime=None):
        if test_datetime is not None:
            return test_datetime - self.date_created
        return now() - self.date_created

    @property
    def contains_a_voucher(self):
        if not self.id:
            return False
        return self.vouchers.exists()

    @property
    def is_submitted(self):
        return self.status == self.SUBMITTED

    @property
    def can_be_edited(self):
        """
        Test if a basket can be edited
        """
        return self.status in self.editable_statuses

    @property
    def currency(self):
        # Since all lines should have the same currency, return the currency of
        # the first one found.
        for line in self.all_lines():
            return line.price_currency

    # =============
    # Query methods
    # =============

    def contains_voucher(self, code):
        """
        Test whether the basket contains a voucher with a given code
        """
        if self.id is None:
            return False
        try:
            self.vouchers.get(code=code)
        except ObjectDoesNotExist:
            return False
        else:
            return True

    def product_quantity(self, product):
        """
        Return the quantity of a product in the basket

        The basket can contain multiple lines with the same product, but
        different options and stockrecords. Those quantities are summed up.
        """
        if self.id:
            matching_lines = self.lines.filter(product=product)
            quantity = matching_lines.aggregate(Sum("quantity"))["quantity__sum"]
            return quantity or 0

        return 0

    def line_quantity(
        self,
        product,
        stockrecord,
        options=None,
    ):
        """
        Return the current quantity of a specific product and options
        """

        ref = self._create_line_reference(product, stockrecord, options)
        try:
            return self.lines.get(line_reference=ref).quantity
        except ObjectDoesNotExist:
            return 0


class Line(models.Model):
    """A line of a basket (product and a quantity)

    Common approaches on ordering basket lines:

        a) First added at top. That's the history-like approach; new items are
           added to the bottom of the list. Changing quantities doesn't impact
           position.
           Oscar does this by default. It just sorts by Line.pk, which is
           guaranteed to increment after each creation.

        b) Last modified at top. That means items move to the top when you add
           another one, and new items are added to the top as well.  Amazon
           mostly does this, but doesn't change the position when you update
           the quantity in the basket view.
           To get this behaviour, change Meta.ordering and optionally do
           something similar on wishlist lines. Order lines should already
           be created in the order of the basket lines, and are sorted by
           their primary key, so no changes should be necessary there.

    """

    basket = models.ForeignKey(
        "basket.Basket",
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name="Корзина",
    )

    # This is to determine which products belong to the same line
    # We can't just use product.id as you can have customised products
    # which should be treated as separate lines.  Set as a
    # SlugField as it is included in the path for certain views.
    line_reference = SlugField("Референс позиции", max_length=128, db_index=True)

    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="basket_lines",
        verbose_name="Товар",
    )

    # We store the stockrecord that should be used to fulfil this line.
    stockrecord = models.ForeignKey(
        "store.StockRecord", on_delete=models.CASCADE, related_name="basket_lines"
    )

    quantity = models.PositiveIntegerField("Количество", default=1)

    price_currency = models.CharField(
        "Валюта", max_length=12, default=get_default_currency
    )
    tax_code = models.CharField("Налоговый код", max_length=64, blank=True, null=True)

    # Track date of first addition
    date_created = models.DateTimeField(
        "Дата создания", auto_now_add=True, db_index=True
    )
    date_updated = models.DateTimeField("Дата изменения", auto_now=True, db_index=True)

    _cached_unit_price = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.discounts = LineDiscountRegistry(self)

    class Meta:
        app_label = "basket"
        # Enforce sorting by order of creation.
        ordering = ["date_created", "pk"]
        unique_together = ("basket", "line_reference")
        verbose_name = "Позиция корзины"
        verbose_name_plural = "Позиции корзины"

    def __str__(self):
        return (
            "Корзина #%(basket_id)d, Товар #%(product_id)d, Количество %(quantity)d"
        ) % {
            "basket_id": self.basket.pk,
            "product_id": self.product.pk,
            "quantity": self.quantity,
        }

    def save(self, *args, **kwargs):
        if not self.basket.can_be_edited:
            raise PermissionDenied(
                ("Вы не можете изменить %s корзину") % (self.basket.status.lower(),)
            )
        return super().save(*args, **kwargs)

    # =============
    # Offer methods
    # =============

    def clear_discount(self):
        """
        Remove any discounts from this line.
        """
        self.discounts = LineDiscountRegistry(self)

    def discount(self, discount_value, affected_quantity, offer=None):
        """
        Apply a discount to this line
        """
        self.discounts.discount(discount_value, affected_quantity, offer)

    def consume(self, quantity, offer=None):
        """
        Mark all or part of the line as 'consumed'

        Consumed items are no longer available to be used in offers.
        """
        return self.discounts.consume(quantity, offer=offer)

    def get_price_breakdown(self):
        """
        Return a breakdown of line prices after discounts have been applied.

        Returns a list of (unit_price, quantity)
        tuples.
        """
        prices = []
        if not self.discount_value:
            prices.append((self.unit_price, self.quantity))
        else:
            # Need to split the discount among the affected quantity
            # of products.
            item_discount = self.discount_value / int(self.discounts.num_consumed())
            prices.append(
                (
                    self.unit_price - item_discount,
                    self.discounts.num_consumed(),
                )
            )
            if self.quantity_without_discount:
                prices.append(
                    (
                        self.unit_price,
                        self.quantity_without_discount,
                    )
                )
        return prices

    # ===============
    # Offer Discounts
    # ===============

    def has_offer_discount(self, offer):
        return self.discounts.num_consumed(offer) > 0

    def quantity_with_offer_discount(self, offer):
        return self.discounts.num_consumed(offer)

    def quantity_without_offer_discount(self, offer):
        return self.discounts.available(offer)

    def is_available_for_offer_discount(self, offer):
        return self.discounts.available(offer) > 0

    def quantity_available_for_offer(self, offer):
        return self.quantity_without_offer_discount(
            offer
        ) + self.quantity_with_offer_discount(offer)

    def check_availability(self):
        """
        Return a warning message about this basket line if one is applicable

        This could be things like the quantity has changed
        """
        availability = self.purchase_info.availability

        if isinstance(availability, Unavailable):
            self.available = False
            self.warning = "Временно не доступен"
            return self.warning

        if isinstance(availability, StockRequired):
            self.available, self.warning = availability.is_purchase_permitted(
                self.quantity
            )
            if not self.available:
                max_quantity = availability.num_available
                if self.quantity > max_quantity:
                    self.quantity = max_quantity
                    self.available = True
                    self.save()
                    
            return self.warning

    def get_options(self):
        return [
            attribute
            for attribute in self.attributes.all()
            if isinstance(attribute.value, list)
        ]

    def get_additions(self):
        return self.attributes.filter(
            additional__isnull=False,
            additional__is_public=True,
            additional__stores__id=self.basket.store_id,
            value__gt=0,
        ).distinct()

    def get_full_name(self):
        if self.product:
            return " | ".join(
                filter(
                    None,
                    [
                        self.product.get_name(),
                        self.variants,
                        self.options,
                        self.additions,
                    ],
                )
            )
        return self.name

    # ==========
    # Properties
    # ==========

    @property
    def has_discount(self):
        return bool(self.discounts.num_consumed())

    @property
    def quantity_with_discount(self):
        return self.discounts.num_consumed()

    @property
    def quantity_without_discount(self):
        return self.discounts.available()

    @property
    def discount_value(self):
        return self.discounts.total

    # pylint: disable=W0201
    @property
    def purchase_info(self):
        """
        Return the stock/price info
        """
        if not hasattr(self, "_info"):
            # Cache the PurchaseInfo instance.
            self._info = self.basket.strategy.fetch_for_line(self, self.stockrecord)
        return self._info

    @property
    def unit_effective_price(self):
        """
        The price to use for offer calculations
        """
        return self.purchase_info.price.effective_price

    @property
    def unit_price(self):
        if self._cached_unit_price is None:
            price_item = self.purchase_info.price.money
            if price_item:
                price_item = price_item + self.additions_total
            self._cached_unit_price = price_item
        return self._cached_unit_price

    @property
    def line_price(self):
        if self.unit_price is not None:
            return self.quantity * self.unit_price

    @property
    def line_price_incl_discounts(self):
        _discounts = self.discounts.total

        if self.line_price is not None and _discounts:
            return max(0, self.line_price - _discounts)

        return self.line_price

    @property
    def name(self):
        return smart_str(self.product)

    @property
    def options(self):
        return "\n".join(
            (
                f"{attr.option.name}: {', '.join(map(str, attr.value))}"
                if isinstance(attr.value, list)
                else f"{attr.option.name}: {attr.value}"
            )
            for attr in self.attributes.filter(option__isnull=False)
        )

    @property
    def additions(self):
        return ", ".join(
            f"{attr.additional.name} ({attr.value} шт)"
            for attr in self.attributes.filter(
                additional__isnull=False,
                additional__is_public=True,
                additional__stores__id=self.basket.store_id,
                value__gt=0,
            ).distinct()
        )

    @property
    def additions_total(self):
        if not self.pk:
            return D("0.00")

        return sum(
            attribute.value * attribute.additional.price
            for attribute in self.attributes.filter(
                additional__isnull=False,
                additional__is_public=True,
                additional__stores__id=self.basket.store_id,
                value__gt=0,
            )
        )

    @property
    def variants(self):
        return self.product.get_variants()

    @property
    def old_price(self):
        if self.stockrecord.old_price:
            return self.stockrecord.old_price + self.additions_total
        return None

    @cached_property
    def has_topping(self):
        return self.product.get_variants() or self.attributes.all()


class LineAttribute(models.Model):
    """
    An attribute of a basket line
    """

    line = models.ForeignKey(
        "basket.Line",
        on_delete=models.CASCADE,
        related_name="attributes",
        verbose_name="Позиция",
    )
    option = models.ForeignKey(
        "catalogue.Option", on_delete=models.CASCADE, verbose_name="Опция", null=True
    )
    additional = models.ForeignKey(
        "catalogue.Additional",
        on_delete=models.CASCADE,
        verbose_name="Дополнительный товар",
        null=True,
    )
    value = models.JSONField("Значение", encoder=DjangoJSONEncoder)

    class Meta:
        app_label = "basket"
        verbose_name = "Атрибут позиции"
        verbose_name_plural = "Атрибуты позиции"
