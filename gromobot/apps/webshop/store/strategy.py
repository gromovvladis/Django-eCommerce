from collections import namedtuple
from decimal import Decimal as D

from core.loading import get_class, get_model
from django.db.models import F, Q, Value
from django.db.models.functions import Coalesce

Unavailable = get_class("webshop.store.availability", "Unavailable")
Available = get_class("webshop.store.availability", "Available")
StockRequiredAvailability = get_class("webshop.store.availability", "StockRequired")
UnavailablePrice = get_class("webshop.store.prices", "Unavailable")
FixedPrice = get_class("webshop.store.prices", "FixedPrice")
TaxInclusiveFixedPrice = get_class("webshop.store.prices", "TaxInclusiveFixedPrice")

StockRecord = get_model("store", "StockRecord")
PurchaseInfo = namedtuple(
    "PurchaseInfo", ["price", "availability", "stockrecord", "stockrecords"]
)


class Selector(object):
    """
    Responsible for returning the appropriate strategy class for a given
    user/session.

    This can be called in three ways:

    #) Passing a request and user. This is for determining
       prices/availability for a normal user browsing the site.

    #) Passing just the user. This is for offline processes that don't
       have a request instance but do know which user to determine prices for.

    #) Passing nothing. This is for offline processes that don't
       correspond to a specific user, e.g., determining a price to store in
       a search index.

    """

    # pylint: disable=unused-argument
    def strategy(self, request=None, user=None, **kwargs):
        """
        Return an instantiated strategy instance
        """
        # Default to the backwards-compatible strategy of picking the first
        # stockrecord but charging zero tax.
        return Default(request, user)


# pylint: disable=unused-argument
class Base(object):
    """
    The base strategy class

    Given a product, strategies are responsible for returning a
    ``PurchaseInfo`` instance which contains:

    - The appropriate stockrecord for this customer
    - A pricing policy instance
    - An availability policy instance
    """

    def __init__(self, request=None, user=None):
        self.request = request
        self.user = request.user if request and request.user.is_authenticated else user

    def fetch_for_product(self, product, stockrecord=None):
        """
        Given a product, return a ``PurchaseInfo`` instance.

        The ``PurchaseInfo`` class is a named tuple with attributes:

        - ``price``: a pricing policy object.
        - ``availability``: an availability policy object.
        - ``stockrecord``: the stockrecord that is being used

        If a stockrecord is passed, return the appropriate ``PurchaseInfo``
        instance for that product and stockrecord is returned.
        """
        raise NotImplementedError(
            "A strategy class must define a fetch_for_product method "
            "for returning the availability and pricing "
            "information."
        )

    def fetch_for_parent(self, product):
        """
        Given a parent product, fetch a ``StockInfo`` instance
        """
        raise NotImplementedError(
            "A strategy class must define a fetch_for_parent method "
            "for returning the availability and pricing "
            "information."
        )

    def fetch_for_parent_detail(self, product):
        """
        Given a parent product, fetch a ``StockInfo`` instance
        """
        raise NotImplementedError(
            "A strategy class must define a fetch_for_parent_detail method "
            "for returning the availability and pricing "
            "information."
        )

    def fetch_for_line(self, line, stockrecord=None):
        """
        Given a basket line instance, fetch a ``PurchaseInfo`` instance.

        This method is provided to allow purchase info to be determined using a
        basket line's attributes.  For instance, "bundle" products often use
        basket line attributes to store SKUs of contained products.  For such
        products, we need to look at the availability of each contained product
        to determine overall availability.
        """
        # Default to ignoring any basket line options as we don't know what to
        # do with them within Oscar - that's up to your project to implement.
        return self.fetch_for_product(line.product)


class Structured(Base):
    """
    A strategy class which provides separate, overridable methods for
    determining the 3 things that a ``PurchaseInfo`` instance requires:

    #) A stockrecord
    #) A pricing policy
    #) An availability policy
    """

    def fetch_for_product(self, product, stockrecord=None):
        """
        Return the appropriate ``PurchaseInfo`` instance.
        This method is not intended to be overridden.
        """
        stockrecords = self.available_stockrecords(product)
        stockrecord = stockrecord or self.select_stockrecord(stockrecords)
        price = self.pricing_policy(stockrecord)
        return PurchaseInfo(
            price=price,
            availability=self.availability_policy(product, stockrecord),
            stockrecord=stockrecord,
            stockrecords=stockrecords,
        )

    def fetch_for_parent(self, product):
        # Select children and associated stockrecords
        stockrecords = self.available_stockrecords(product)
        return PurchaseInfo(
            price=self.parent_min_pricing_policy(stockrecords),
            availability=self.parent_availability_policy(product, stockrecords),
            stockrecord=None,
            stockrecords=stockrecords,
        )

    def fetch_for_parent_detail(self, product):
        # Select children and associated stockrecords
        stockrecords = self.available_stockrecords(product)
        return PurchaseInfo(
            price=self.parent_pricing_policy(product, stockrecords),
            availability=self.parent_availability_policy(product, stockrecords),
            stockrecord=None,
            stockrecords=stockrecords,
        )

    def select_stockrecord(self, stockrecords):
        """
        Select the appropriate stockrecord
        """
        raise NotImplementedError(
            "A structured strategy class must define a 'select_stockrecord' method"
        )

    def pricing_policy(self, stockrecord):
        """
        Return the appropriate pricing policy
        """
        raise NotImplementedError(
            "A structured strategy class must define a 'pricing_policy' method"
        )

    def parent_pricing_policy(self, product, children_stock):
        raise NotImplementedError(
            "A structured strategy class must define a "
            "'parent_pricing_policy' method"
        )

    def parent_min_pricing_policy(self, children_stock):
        raise NotImplementedError(
            "A structured strategy class must define a "
            "'parent_min_pricing_policy' method"
        )

    def availability_policy(self, product, stockrecord):
        """
        Return the appropriate availability policy
        """
        raise NotImplementedError(
            "A structured strategy class must define a 'availability_policy' method"
        )

    def parent_availability_policy(self, product, children_stock):
        raise NotImplementedError(
            "A structured strategy class must define a "
            "'parent_availability_policy' method"
        )

    def available_stockrecords(self, product):
        raise NotImplementedError(
            "A structured strategy class must define a "
            "'available_stockrecords' method"
        )

    def is_available(self, product):
        raise NotImplementedError(
            "A structured strategy class must define a " "'is_available' method"
        )


class UseStoreStockRecord:
    """
    Stockrecord selection mixin for use with the ``Structured`` base strategy.
    This mixin picks the first (normally only) stockrecord to fulfil a product.
    """

    def select_stockrecord(self, stockrecords):
        return stockrecords.filter(store_id=self.get_store_id()).first()

    def get_store_id(self):
        if not hasattr(self, "_cached_store_id"):
            self._cached_store_id = self.request.store.id
        return self._cached_store_id

    def available_stockrecords(self, product):
        filter_field = "product__parent_id" if product.is_parent else "product_id"
        base_query = Q(**{filter_field: product.id, "is_public": True})
        if product.get_product_class().track_stock:
            base_query &= Q(num_in_stock__gt=Coalesce(F("num_allocated"), Value(0)))

        return StockRecord.objects.filter(base_query)

    def is_available(self, product):
        if not hasattr(self, "_cached_availability"):
            self._cached_availability = self.available_stockrecords(product).exists()
        return self._cached_availability


class StockRequired(object):
    """
    Availability policy mixin for use with the ``Structured`` base strategy.
    This mixin ensures that a product can only be bought if it has stock
    available (if stock is being tracked).
    """

    def availability_policy(self, product, stockrecord):
        if not stockrecord or not stockrecord.is_public:
            return Unavailable()
        if not product.get_product_class().track_stock:
            return Available()
        else:
            return StockRequiredAvailability(stockrecord.net_stock_level)

    def parent_availability_policy(self, product, stockrecords):
        # A parent product is available if one of its children is
        for stockrecord in stockrecords:
            policy = self.availability_policy(product, stockrecord)
            if policy.is_available_to_buy:
                return Available()
        return Unavailable()


class PricingPolicy(object):
    """
    Pricing policy mixin for use with the ``Structured`` base strategy.
    This mixin specifies zero tax and uses the ``price`` from the
    stockrecord.
    """

    def pricing_policy(self, stockrecord):
        # Check stockrecord has the appropriate data
        if not stockrecord or stockrecord.price is None:
            return UnavailablePrice()

        return FixedPrice(
            currency=stockrecord.price_currency,
            money=stockrecord.price,
            old_price=stockrecord.old_price,
        )

    def parent_pricing_policy(self, product, stockrecords):
        if not stockrecords:
            return UnavailablePrice()

        first_child = product.children.order_by("-order").first()
        stockrecord = next(
            (sr for sr in stockrecords if sr.product == first_child), None
        )

        if stockrecord:
            return FixedPrice(
                currency=stockrecord.price_currency,
                money=stockrecord.price,
                old_price=stockrecord.old_price,
            )

        stockrecord = stockrecords[0]
        return FixedPrice(
            currency=stockrecord.price_currency,
            money=None,
            old_price=None,
        )

    def parent_min_pricing_policy(self, stockrecords):
        if not stockrecords:
            return UnavailablePrice()

        stockrecord = stockrecords.order_by("price").first()
        if stockrecord:
            return FixedPrice(
                currency=stockrecord.price_currency,
                money=stockrecord.price,
                old_price=stockrecord.old_price,
            )

        return UnavailablePrice()


class Default(UseStoreStockRecord, StockRequired, PricingPolicy, Structured):
    """
    Default stock/price strategy that uses the first found stockrecord for a
    product, ensures that stock is available (unless the product class
    indicates that we don't need to track stock) and charges zero tax.
    """

    rate = D(0)
