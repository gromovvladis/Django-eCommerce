from oscar.apps.shipping.methods import NoShippingRequired


class CheckoutSessionData(object):
    """
    Responsible for marshalling all the checkout session data

    Multi-stage checkouts often require several forms to be submitted and their
    data persisted until the final order is placed. This class helps store and
    organise checkout form data until it is required to write out the final
    order.
    """

    SESSION_KEY = "checkout_data"

    def __init__(self, request):
        self.request = request
        if self.SESSION_KEY not in self.request.session:
            self.request.session[self.SESSION_KEY] = {}

    def _check_namespace(self, namespace):
        """
        Ensure a namespace within the session dict is initialised
        """
        key = self.request.session[self.SESSION_KEY]
        if namespace not in self.request.session[self.SESSION_KEY]:
            self.request.session[self.SESSION_KEY][namespace] = {}

    def _get(self, namespace, key, default=None):
        """
        Return a value from within a namespace
        """
        self._check_namespace(namespace)
        if key in self.request.session[self.SESSION_KEY][namespace]:
            return self.request.session[self.SESSION_KEY][namespace][key]
        return default

    def _set(self, namespace, key, value):
        """
        Set a namespaced value
        """
        self._check_namespace(namespace)
        self.request.session[self.SESSION_KEY][namespace][key] = value
        self.request.session.modified = True

    def _unset(self, namespace, key):
        """
        Remove a namespaced value
        """
        self._check_namespace(namespace)
        if key in self.request.session[self.SESSION_KEY][namespace]:
            del self.request.session[self.SESSION_KEY][namespace][key]
            self.request.session.modified = True

    def _flush_namespace(self, namespace):
        """
        Flush a namespace
        """
        self.request.session[self.SESSION_KEY][namespace] = {}
        self.request.session.modified = True

    def flush(self):
        """
        Flush all session data
        """
        self.request.session[self.SESSION_KEY] = {}

    # Shipping address
    # ================
    # Options:
    # 1. No shipping required (eg digital products)
    # 2. Ship to session address (entered in a form)
    # 3. Ship to an address book address (address chosen from list)

    def reset_shipping_data(self):
        self._flush_namespace("shipping")

    def set_session_address(self, address_fields):
        """
        Use a manually entered address as the shipping address
        """
        self._unset("shipping", "session_address_fields")
        self._set("shipping", "session_address_fields", address_fields)

    def session_shipping_address_fields(self):
        """
        Return shipping address fields
        """
        return self._get("shipping", "session_address_fields")

    def is_shipping_address_set(self):
        """
        Test whether a shipping address has been stored in the session.

        This can be from a session address or re-using an existing address.
        """
        shipping_method = self.shipping_method_code()
        if shipping_method == NoShippingRequired().code:
            return True

        return self.session_shipping_address_fields()

    # Shipping method
    # ===============

    def use_free_shipping(self):
        """
        Set "Бесплатная доставка" code to session
        """
        self._set("shipping", "method_code", "__free__")

    def use_shipping_method(self, code):
        """
        Set shipping method code to session
        """
        self._set("shipping", "method_code", code)

    # pylint: disable=unused-argument
    def shipping_method_code(self):
        """
        Return the shipping method code
        """
        return self._get("shipping", "method_code")

    def is_shipping_method_set(self):
        """
        Test if a valid shipping method is stored in the session
        """
        return self.shipping_method_code() is not None

    # Submission methods
    # ==================

    def set_order_number(self, order_number):
        self._set("submission", "order_number", order_number)

    def get_order_number(self):
        return self._get("submission", "order_number")

    def set_submitted_basket(self, basket):
        self._set("submission", "basket_id", basket.id)

    def get_submitted_basket_id(self):
        return self._get("submission", "basket_id")

    # Payment methods
    # ===============

    def pay_by(self, method):
        self._set("payment", "method", method)

    def payment_method(self):
        return self._get("payment", "method")

    # Order note
    # ==================

    def set_order_note(self, order_note):
        self._set("submission", "order_note", order_note)

    def order_note(self):
        return self._get(
            "submission",
            "order_note",
        )

    # Order time
    # ==================

    def set_order_time(self, order_time):
        self._set("submission", "order_time", order_time.isoformat())

    def order_time(self):
        return self._get(
            "submission",
            "order_time",
        )

    # email or charge
    # ==================

    def set_email_or_change(self, email_or_change):
        self._set("submission", "email_or_change", email_or_change)

    def email_or_change(self):
        return self._get(
            "submission",
            "email_or_change",
        )
