from datetime import datetime
from decimal import Decimal as D

from apps.webshop.shipping.methods import NoShippingRequired
from apps.webshop.shipping.utils import is_valid_order_time
from core import prices
from core.loading import get_class, get_model
from django import http
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from . import exceptions

Repository = get_class("webshop.shipping.repository", "Repository")
SurchargeApplicator = get_class("webshop.checkout.applicator", "SurchargeApplicator")
OrderTotalCalculator = get_class("webshop.checkout.calculators", "OrderTotalCalculator")
CheckoutSessionData = get_class("webshop.checkout.utils", "CheckoutSessionData")
Map = get_class("webshop.shipping.maps", "Map")
ZonesUtils = get_class("webshop.shipping.zones", "ZonesUtils")

ShippingAddress = get_model("order", "ShippingAddress")
UserAddress = get_model("address", "UserAddress")


class CheckoutSessionMixin(object):
    """
    Mixin to provide common functionality shared between checkout views.

    All checkout views subclass this mixin. It ensures that all relevant
    checkout information is available in the template context.
    """

    # A pre-condition is a condition that MUST be met in order for a view
    # to be available. If it isn't then the customer should be redirected
    # to a view *earlier* in the chain.
    # pre_conditions is a list of method names that get executed before the
    # normal flow of the view. Each method should check some condition has been
    # met. If not, then an exception is raised that indicates the URL the
    # customer will be redirected to.

    pre_conditions = None

    # A *skip* condition is a condition that MUST NOT be met in order for a
    # view to be available. If the condition is met, this means the view MUST
    # be skipped and the customer should be redirected to a view *later* in
    # the chain.
    # Skip conditions work similar to pre-conditions, and get evaluated after
    # pre-conditions have been evaluated.
    skip_conditions = None

    def dispatch(self, request, *args, **kwargs):
        # Assign the checkout session manager so it's available in all checkout
        # views.
        self.checkout_session = CheckoutSessionData(request)

        # Check if this view should be skipped
        try:
            self.check_skip_conditions(request)
        except exceptions.PassedSkipCondition as e:
            return http.HttpResponseRedirect(e.url)

        # Enforce any pre-conditions for the view.
        try:
            self.check_pre_conditions(request)
        except exceptions.FailedPreCondition as e:
            for message in e.messages:
                messages.warning(request, message)
            return http.HttpResponseRedirect(e.url)

        return super().dispatch(request, *args, **kwargs)

    def check_pre_conditions(self, request):
        pre_conditions = self.get_pre_conditions(request)
        for method_name in pre_conditions:
            if not hasattr(self, method_name):
                raise ImproperlyConfigured(
                    "Нет метода '%s' чтобы вызвать как 'pre-condition'." % (method_name)
                )
            getattr(self, method_name)(request)

    def get_pre_conditions(self, request):
        """
        Return the pre-condition method names to run for this view
        """
        if self.pre_conditions is None:
            return []
        return self.pre_conditions

    def check_skip_conditions(self, request):
        skip_conditions = self.get_skip_conditions(request)
        for method_name in skip_conditions:
            if not hasattr(self, method_name):
                raise ImproperlyConfigured(
                    "Нет метода '%s' чтобы вызвать как 'skip-condition'."
                    % (method_name)
                )
            getattr(self, method_name)(request)

    def get_skip_conditions(self, request):
        """
        Return the skip-condition method names to run for this view
        """
        if self.skip_conditions is None:
            return []
        return self.skip_conditions

    # Re-usable pre-condition validators

    def check_basket_is_not_empty(self, request):
        if request.basket.is_empty:
            raise exceptions.FailedPreCondition(
                url=reverse("basket:summary"),
                message="Для оформления заказа вам необходимо добавить товары в корзину.",
            )

    def delete_non_valid_lines(self, request):
        lines = self.request.basket.all_lines()
        for line in lines:
            is_available = line.purchase_info.availability.is_available_to_buy
            if line.quantity == 0 or not is_available:
                try:
                    line.delete()
                    request.basket._lines = None
                    request.basket._filtered_lines = None
                except Exception:
                    pass

    def check_basket_is_valid(self, request):
        """
        Check that the basket is permitted to be submitted as an order. That
        is, all the basket lines are available to buy - nothing has gone out of
        stock since it was added to the basket.
        """
        messages_list = []
        strategy = request.strategy
        for line in request.basket.all_lines():
            result = strategy.fetch_for_line(line)
            is_permitted, reason = result.availability.is_purchase_permitted(
                line.quantity
            )
            if not is_permitted:
                # Create a more meaningful message to show on the basket page
                msg = (
                    '"%(name)s" больше нельзя купить (%(reason)s).'
                    # 'Пожалуйста, скорректируйте корзину, чтобы продолжить'
                ) % {"name": line.product.get_name(), "reason": reason}
                messages_list.append(msg)
        if messages_list:
            raise exceptions.FailedPreCondition(
                url=reverse("basket:summary"), messages=messages_list
            )

    def check_user_phone_is_captured(self, request):
        if not request.user.is_authenticated:
            raise exceptions.FailedPreCondition(
                url=reverse("checkout:index"),
                message="Пожалуйста, войдите в систему, чтобы разместить заказ.",
            )

    def check_shipping_data_is_captured(self, request):
        if not request.basket.is_shipping_required():
            # Even without shipping being required, we still need to check that
            # a shipping method code has been set.
            if not self.checkout_session.is_shipping_method_set():
                messages.error(self.request, "Выберите способ доставки.")
                raise exceptions.FailedPreCondition(
                    url=reverse("checkout:checkoutview"),
                )
            return

        shipping_method = self.get_shipping_method(request.basket)
        if shipping_method and shipping_method.code == NoShippingRequired().code:
            return

        # Basket requires shipping: check address and method are captured and
        # valid.
        self.check_a_valid_shipping_address_is_captured()
        self.check_a_valid_shipping_method_is_captured()

    def check_a_valid_shipping_address_is_captured(self):
        # Check that shipping address has been completed
        if not self.checkout_session.is_shipping_address_set():
            raise exceptions.FailedPreCondition(
                url=reverse("checkout:checkoutview"),
                message="Пожалуйста, укажите адрес доставки.",
            )

    def check_a_valid_shipping_method_is_captured(self):
        # Check that shipping method has been set
        if not self.checkout_session.is_shipping_method_set():
            raise exceptions.FailedPreCondition(
                url=reverse("checkout:shipping-method"),
                message="Пожалуйста, выберите способ доставки.",
            )

    def check_payment_method_is_captured(self, request):
        payment_method = self.checkout_session.payment_method()
        if not payment_method:
            raise exceptions.FailedPreCondition(
                url=reverse("checkout:checkoutview"),
                message="Пожалуйста, укажите метод оплаты.",
            )

    def check_order_time_is_captured(self, request):
        order_time = self.get_order_time()
        shipping_method = self.checkout_session.shipping_method_code()
        is_valid = is_valid_order_time(order_time, shipping_method)

        if not is_valid:
            raise exceptions.FailedPreCondition(
                url=reverse("checkout:checkoutview"),
                message="Данное время заказа более недоступно. Пожалуйста, повторите оформление заказа.",
            )

    # Helpers

    def build_submission(self, **kwargs):
        """
        Return a dict of data that contains everything required for an order
        submission.  This includes payment details (if any).

        This can be the right place to perform tax lookups and apply them to
        the basket.
        """
        # Pop the basket if there is one, because we pass it as a positional
        # argument to methods below
        basket = kwargs.pop("basket", self.request.basket)
        shipping_address = self.get_shipping_address(basket)
        shipping_method = self.get_shipping_method(basket, shipping_address)
        order_note = self.get_order_note()
        order_time = self.get_order_time()
        email_or_change = self.get_email_or_change()

        if not shipping_method:
            # total = shipping_charge = surcharges = min_order = None
            shipping_charge = surcharges = min_order = prices.Price(
                currency=basket.currency, money=D("0.00")
            )
        elif shipping_method.code == NoShippingRequired().code:
            shipping_address = None
            shipping_charge = min_order = prices.Price(
                currency=basket.currency, money=D("0.00")
            )

        elif shipping_address:
            if shipping_address.coords_lat and shipping_address.coords_long:
                shipping_charge, min_order = shipping_method.calculate(
                    basket, shipping_address
                )
            elif shipping_address.line1:
                map = Map()
                geoObject = map.geocode(address=shipping_address.line1)
                coords = map.coordinates(geoObject)
                zona_id = ZonesUtils.zona_id(coords)
                shipping_charge, min_order = shipping_method.calculate(basket, zona_id)

        submission = {
            "user": self.request.user,
            "basket": basket,
            "shipping_address": shipping_address,
            "shipping_method": shipping_method,
            "order_note": order_note,
            "order_time": order_time,
            "email_or_change": email_or_change,
            "shipping_charge": shipping_charge,
            "order_kwargs": {},
            "payment_kwargs": {},
        }

        surcharges = SurchargeApplicator(
            self.request, submission
        ).get_applicable_surcharges(
            self.request.basket, shipping_charge=shipping_charge
        )
        total = self.get_order_totals(
            basket, shipping_charge=shipping_charge, surcharges=surcharges, **kwargs
        )

        submission["order_total"] = total
        submission["surcharges"] = surcharges

        # Allow overrides to be passed in
        submission.update(kwargs)

        return submission

    def get_shipping_address(self, basket):
        """
        Return the (unsaved) shipping address for this checkout session.

        If the shipping address was entered manually, then we instantiate a
        ``ShippingAddress`` model with the appropriate form data (which is
        saved in the session).

        If the shipping address was selected from the user's address book,
        then we convert the ``UserAddress`` to a ``ShippingAddress``.

        The ``ShippingAddress`` instance is not saved as sometimes you need a
        shipping address instance before the order is placed.  For example, if
        you are submitting fraud information as part of a payment request.

        The ``OrderPlacementMixin.create_shipping_address`` method is
        responsible for saving a shipping address when an order is placed.
        """
        if not basket.is_shipping_required():
            return None

        addr_data = self.checkout_session.session_shipping_address_fields()
        if addr_data:
            # Load address data into a blank shipping address model
            return ShippingAddress(**addr_data)
        return None

    def get_shipping_method(self, basket, shipping_address=None, **kwargs):
        """
        Return the selected shipping method instance from this checkout session

        The shipping address is passed as we need to check that the method
        stored in the session is still valid for the shipping address.
        """
        code = self.checkout_session.shipping_method_code()
        methods = Repository().get_shipping_methods(
            basket=basket,
            user=self.request.user,
            shipping_addr=shipping_address,
            request=self.request,
        )
        for method in methods:
            if method.code == code:
                return method

    # =======================

    def get_order_note(self, **kwargs):
        return self.checkout_session.order_note()

    def get_order_time(self, **kwargs):
        return datetime.fromisoformat(self.checkout_session.order_time())

    def get_email_or_change(self, **kwargs):
        return self.checkout_session.email_or_change()

    # ========================

    def get_order_totals(self, basket, shipping_charge, surcharges=None, **kwargs):
        """
        Returns the total for the order with and without t
        """
        return OrderTotalCalculator(self.request).calculate(
            basket, shipping_charge, surcharges, **kwargs
        )
