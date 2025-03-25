from decimal import Decimal as D

from apps.webshop.shipping.methods import OfferDiscount
from core.loading import get_classes
from django.core.exceptions import ImproperlyConfigured

ZonaBasedShipping, NoShippingRequired = get_classes(
    "webshop.shipping.methods", ["ZonaBasedShipping", "NoShippingRequired"]
)


class Repository(object):
    """
    Repository class responsible for returning ShippingMethod
    objects for a given user, basket etc
    """

    # We default to just free shipping. Customise this class and override this
    # property to add your own shipping methods. This should be a list of
    # instantiated shipping methods.

    methods = (ZonaBasedShipping(True), NoShippingRequired(5))  # first if default

    # API

    def get_shipping_methods(self, basket, shipping_addr=None, **kwargs):
        """
        Return a list of all applicable shipping method instances for a given
        basket, address etc.
        """
        if not basket.is_shipping_required():
            # Special case! Baskets that don't require shipping get a special
            # shipping method.
            return [NoShippingRequired()]

        methods = self.get_available_shipping_methods(
            basket=basket, shipping_addr=shipping_addr, **kwargs
        )
        if basket.has_shipping_discounts:
            methods = self.apply_shipping_offers(basket, methods)
        return methods

    def get_default_shipping_method(self, basket, shipping_addr=None, **kwargs):
        """
        Return a 'default' shipping method to show on the basket page to give
        the customer an indication of what their order will cost.
        """
        shipping_methods = self.get_shipping_methods(
            basket, shipping_addr=shipping_addr, **kwargs
        )
        if len(shipping_methods) == 0:
            raise ImproperlyConfigured("Вам необходимо определить способы доставки")

        # Assume first returned method is default
        return shipping_methods[0]

    def get_shipping_method(self, method):

        shipping_method = None

        for mtd in self.methods:
            if mtd.code == method:
                shipping_method = mtd
                break

        if shipping_method is None:
            raise ImproperlyConfigured("Нет такого метода доставки")

        # Assume first returned method is default
        return shipping_method

    # Helpers

    # pylint: disable=unused-argument
    def get_available_shipping_methods(self, basket, shipping_addr=None, **kwargs):
        """
        Return a list of all applicable shipping method instances for a given
        basket, address etc. This method is intended to be overridden.
        """
        return self.methods

    def apply_shipping_offers(self, basket, methods):
        """
        Apply shipping offers to the passed set of methods
        """
        # We default to only applying the first shipping discount.
        offer = basket.shipping_discounts[0]["offer"]
        return [self.apply_shipping_offer(basket, method, offer) for method in methods]

    def apply_shipping_offer(self, basket, method, offer):
        """
        Wrap a shipping method with an offer discount wrapper (as long as the
        shipping charge is non-zero).
        """
        # If the basket has qualified for shipping discount, wrap the shipping
        # method with a decorating class that applies the offer discount to the
        # shipping charge.
        charge = method.calculate(basket)
        if charge.money == D("0.00"):
            # No need to wrap zero shipping charges
            return method

        return OfferDiscount(method, offer)
