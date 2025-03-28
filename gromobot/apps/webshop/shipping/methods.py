from decimal import Decimal as D

from core import prices
from core.loading import get_class, get_model

ZonesUtils = get_class("webshop.shipping.zones", "ZonesUtils")
Map = get_class("webshop.shipping.maps", "Map")

ShippingZona = get_model("shipping", "ShippingZona")


class Base(object):
    """
    Shipping method interface class

    This is the superclass to the classes in this module. This allows
    using all shipping methods interchangeably (aka polymorphism).

    The interface is all properties.
    """

    #: Used to store this method in the session.  Each shipping method should
    #:  have a unique code.
    code = "__default__"

    default_selected = False

    #: The name of the shipping method, shown to the customer during checkout
    name = "Default shipping"

    #: A more detailed description of the shipping method shown to the customer
    #:  during checkout.  Can contain HTML.
    description = ""

    #: Whether the charge includes a discount
    is_discounted = False

    def calculate(self, basket, address=None):
        """
        Return the shipping charge for the given basket
        """
        raise NotImplementedError

    # pylint: disable=unused-argument
    def discount(self, basket):
        """
        Return the discount on the standard shipping charge
        """
        # The regular shipping methods don't add a default discount.
        # For offers and vouchers, the discount will be provided
        # by a wrapper that Repository.apply_shipping_offer() adds.
        return D("0.00")


class Free(Base):
    """
    This shipping method specifies that shipping is free.
    """

    def __init__(self, default_selected=False):
        self.default_selected = default_selected

    code = "free-shipping"
    name = "Бесплатная доставка"

    def calculate(self, basket, address=None):
        """ "Returns the shipping charges and minimum order price"""
        # If the charge is free then tax must be free (musn't it?) and so we
        # immediately set the tax to zero
        return prices.Price(currency=basket.currency, money=D("0.00")), prices.Price(
            currency=basket.currency, money=D("0.00")
        )


class NoShippingRequired(Free):
    """
    This shipping method indicates that shipping costs a fixed price and
    requires no special calculation.
    """

    code = "self-pick-up"
    name = "Самовывоз"

    # Charges can be either declared by subclassing and overriding the
    # class attributes or by passing them to the constructor
    pickup_discount = None

    def __init__(self, pickup_discount=0, default_selected=False):
        super().__init__()  # Вызов конструктора родительского класса (если необходимо)
        if pickup_discount is not None:
            self.pickup_discount = pickup_discount
        self.default_selected = default_selected

    def calculate(self, basket, address=None):
        """Returns the shipping charges and minimum order price"""
        discount = basket.total * self.pickup_discount / 100
        shipping_charge = prices.Price(currency=basket.currency, money=-discount)
        minimum_order_price = prices.Price(currency=basket.currency, money=D("0"))
        return shipping_charge, minimum_order_price


class FixedPrice(Base):
    """
    This shipping method indicates that shipping costs a fixed price and
    requires no special calculation.
    """

    code = "fixed-price-shipping"
    name = "Доставка с фиксированной ценой"

    # Charges can be either declared by subclassing and overriding the
    # class attributes or by passing them to the constructor
    charge = None

    def __init__(self, charge=None, default_selected=False):
        if charge is not None:
            self.charge = charge
        self.default_selected = default_selected

    def calculate(self, basket, address=None):
        """Returns the shipping charges and minimum order price"""
        shipping_charge = prices.Price(currency=basket.currency, money=self.charge)
        minimum_order_price = prices.Price(currency=basket.currency, money=D("700.00"))
        return shipping_charge, minimum_order_price


class ZonaBasedShipping(Base):
    """
    This shipping method indicates that shipping costs a fixed price and
    requires no special calculation.
    """

    code = "zona-shipping"
    name = "Доставка"

    def __init__(self, default_selected=False):
        self.default_selected = default_selected
        self.zones_utils = ZonesUtils()

    def calculate(self, basket, address=None):
        """ "Returns the shipping charges and minimum order price"""

        if not address or not address.line1:
            return self._get_default_shipping_price(basket)

        if not address.coords_lat or not address.coords_long:
            self._get_coords(address)

        zona_id = self.zones_utils.get_zona_id(
            [address.coords_lat, address.coords_long]
        )
        return self.calculate_from_zona_id(basket, zona_id)

    def calculate_from_zona_id(self, basket, zona_id):
        shipping_charge = self.zones_utils.zona_charge(zona_id)
        min_order = self.zones_utils.min_order(zona_id)
        shipping_charge_price = prices.Price(
            currency=basket.currency, money=shipping_charge
        )
        minimum_order_price = prices.Price(currency=basket.currency, money=min_order)
        return shipping_charge_price, minimum_order_price

    def _get_coords(self, shipping_address):
        """Retrieves coordinates for the shipping address using geocoding."""
        map = Map()
        geoObject = map.geocode(address=shipping_address.line1)
        coords = map.coordinates(geoObject)

        # Сохраняем координаты в адресе
        shipping_address.coords_lat = coords[0]
        shipping_address.coords_long = coords[1]
        shipping_address.save()

    def _get_default_shipping_price(self, basket):
        """Returns the default shipping charge and minimum order price."""
        shipping_charge = prices.Price(currency=basket.currency, money=0)
        minimum_order_price = prices.Price(currency=basket.currency, money=0)
        return shipping_charge, minimum_order_price


# pylint: disable=abstract-method
class OfferDiscount(Base):
    """
    Wrapper class that applies a discount to an existing shipping
    method's charges.
    """

    is_discounted = True

    def __init__(self, method, offer, default_selected=False):
        self.method = method
        self.offer = offer
        self.default_selected = default_selected

    # Forwarded properties

    @property
    def code(self):
        """
        Returns the :py:attr:`code <apps.webshop.shipping.methods.Base.code>` of the wrapped shipping method.
        """
        return self.method.code

    @property
    def name(self):
        """
        Returns the :py:attr:`name <apps.webshop.shipping.methods.Base.name>` of the wrapped shipping method.
        """
        return self.method.name

    @property
    def discount_name(self):
        """
        Returns the :py:attr:`name <apps.webshop.offer.models.BaseOfferMixin.name>` of the applied Offer.
        """
        return self.offer.name

    @property
    def description(self):
        """
        Returns the :py:attr:`description <.Base.description>` of the wrapped shipping method.
        """
        return self.method.description

    def calculate_excl_discount(self, basket, zona_id):
        """
        Returns the shipping charge for the given basket without
        discount applied.
        """
        return self.method.calculate_from_zona_id(basket, zona_id)
