from decimal import Decimal as D
from oscar.core import prices


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

    def calculate(self, basket):
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

    def calculate(self, basket):
        # If the charge is free then tax must be free (musn't it?) and so we
        # immediately set the tax to zero
        return prices.Price(currency=basket.currency, money=D("0.00"))


class FixedDiscount(Base):
    """
    This is a special shipping method that indicates that no shipping is
    actually required (e.g. for digital goods).
    """

    code = "no-shipping-required"
    name = "Доставка не нужна"




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
        if pickup_discount is not None:
            self.pickup_discount = pickup_discount
        self.default_selected = default_selected

    def calculate(self, basket):
        discount = basket.total * self.pickup_discount / 100
        return prices.Price(
            currency=basket.currency,
            money= -discount,
        )

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

    def calculate(self, basket):
        return prices.Price(
            currency=basket.currency,
            money=self.charge,
        )

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
        Returns the :py:attr:`code <oscar.apps.shipping.methods.Base.code>` of the wrapped shipping method.
        """
        return self.method.code

    @property
    def name(self):
        """
        Returns the :py:attr:`name <oscar.apps.shipping.methods.Base.name>` of the wrapped shipping method.
        """
        return self.method.name

    @property
    def discount_name(self):
        """
        Returns the :py:attr:`name <oscar.apps.offer.abstract_models.BaseOfferMixin.name>` of the applied Offer.
        """
        return self.offer.name

    @property
    def description(self):
        """
        Returns the :py:attr:`description <.Base.description>` of the wrapped shipping method.
        """
        return self.method.description

    def calculate_excl_discount(self, basket):
        """
        Returns the shipping charge for the given basket without
        discount applied.
        """
        return self.method.calculate(basket)
