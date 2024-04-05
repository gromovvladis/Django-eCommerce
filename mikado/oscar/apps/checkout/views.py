import logging
from urllib.parse import quote

from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views import generic

from oscar.core.loading import get_class, get_classes, get_model

from . import signals

GatewayForm, CheckoutForm = get_classes(
    "checkout.forms", ["GatewayForm", "CheckoutForm"]
)
UserAddressForm = get_class("address.forms", "UserAddressForm")
Repository = get_class("shipping.repository", "Repository")
RedirectRequired, UnableToTakePayment, PaymentError = get_classes(
    "payment.exceptions", ["RedirectRequired", "UnableToTakePayment", "PaymentError"]
)
UnableToPlaceOrder = get_class("order.exceptions", "UnableToPlaceOrder")
OrderPlacementMixin = get_class("checkout.mixins", "OrderPlacementMixin")
CheckoutSessionMixin = get_class("checkout.session", "CheckoutSessionMixin")
NoShippingRequired = get_class("shipping.methods", "NoShippingRequired")
Order = get_model("order", "Order")
ShippingAddress = get_model("order", "ShippingAddress")
UserAddress = get_model("address", "UserAddress")

#vlad promocode 
from django.views.generic import FormView, View
from oscar.apps.basket.signals import voucher_addition, voucher_removal
Applicator = get_class("offer.applicator", "Applicator")
from oscar.core.utils import is_ajax, redirect_to_referrer, safe_referrer
from django.core.exceptions import ObjectDoesNotExist
BasketVoucherForm = get_class("basket.forms", "BasketVoucherForm")

# Standard logger for checkout events
logger = logging.getLogger("oscar.checkout")


class IndexView(CheckoutSessionMixin, generic.FormView):
    """
    First page of the checkout.  We prompt user to either sign in, or
    to proceed as a guest (where we still collect their email address).
    """

    template_name = "oscar/checkout/gateway.html"
    form_class = GatewayForm
    success_url = reverse_lazy("checkout:checkoutview")
    pre_conditions = ["check_basket_is_not_empty", "check_basket_is_valid"]

    def get(self, request, *args, **kwargs):
        # We redirect immediately to shipping address stage if the user is
        # signed in.
        if request.user.is_authenticated:
            # We raise a signal to indicate that the user has entered the
            # checkout process so analytics tools can track this event.
            signals.start_checkout.send_robust(sender=self, request=request)
            return self.get_success_response()
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        email = self.checkout_session.get_guest_email()
        if email:
            kwargs["initial"] = {
                "username": email,
            }
        return kwargs

    def form_valid(self, form):
        if form.is_guest_checkout() or form.is_new_account_checkout():
            email = form.cleaned_data["username"]
            self.checkout_session.set_guest_email(email)

            # We raise a signal to indicate that the user has entered the
            # checkout process by specifying an email address.
            signals.start_checkout.send_robust(
                sender=self, request=self.request, email=email
            )

            if form.is_new_account_checkout():
                messages.info(
                    self.request,
                    _(
                        "Create your account and then you will be redirected "
                        "back to the checkout process"
                    ),
                )
                self.success_url = "%s?next=%s&email=%s" % (
                    reverse("customer:register"),
                    # reverse("checkout:shipping-address"),
                    reverse("checkout:checkoutview"),
                    quote(email),
                )
        else:
            user = form.get_user()
            login(self.request, user)

            # We raise a signal to indicate that the user has entered the
            # checkout process.
            signals.start_checkout.send_robust(sender=self, request=self.request)

        return redirect(self.get_success_url())

    def get_success_response(self):
        return redirect(self.get_success_url())


# ================
# SHIPPING ADDRESS
# ================


class UserAddressUpdateView(CheckoutSessionMixin, generic.UpdateView):
    """
    Update a user address
    """

    template_name = "oscar/checkout/user_address_form.html"
    form_class = UserAddressForm
    success_url = reverse_lazy("checkout:checkoutview")

    def get_queryset(self):
        return self.request.user.addresses.all()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        messages.info(self.request, _("Address saved"))
        return super().get_success_url()


class UserAddressDeleteView(CheckoutSessionMixin, generic.DeleteView):
    """
    Delete an address from a user's address book.
    """

    template_name = "oscar/checkout/user_address_delete.html"
    # success_url = reverse_lazy("checkout:shipping-address")
    success_url = reverse_lazy("checkout:checkoutview")

    def get_queryset(self):
        return self.request.user.addresses.all()

    def get_success_url(self):
        messages.info(self.request, _("Address deleted"))
        return super().get_success_url()


# =========
# Thank you
# =========


class ThankYouView(generic.DetailView):
    """
    Displays the 'thank you' page which summarises the order just submitted.
    """

    template_name = "oscar/checkout/thank_you.html"
    context_object_name = "order"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            return redirect(settings.OSCAR_HOMEPAGE)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        # We allow superusers to force an order thank-you page for testing
        order = None
        if self.request.user.is_superuser:
            kwargs = {}
            if "order_number" in self.request.GET:
                kwargs["number"] = self.request.GET["order_number"]
            elif "order_id" in self.request.GET:
                kwargs["id"] = self.request.GET["order_id"]
            order = Order._default_manager.filter(**kwargs).first()

        if not order:
            if "checkout_order_id" in self.request.session:
                order = Order._default_manager.filter(
                    pk=self.request.session["checkout_order_id"]
                ).first()
        return order

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        # Remember whether this view has been loaded.
        # Only send tracking information on the first load.
        key = "order_{}_thankyou_viewed".format(ctx["order"].pk)
        if not self.request.session.get(key, False):
            self.request.session[key] = True
            ctx["send_analytics_event"] = True
        else:
            ctx["send_analytics_event"] = False

        return ctx



# =========
# Voucher
# =========


class VoucherAddView(FormView):
    form_class = BasketVoucherForm
    voucher_model = get_model("voucher", "voucher")
    add_signal = voucher_addition

    def get(self, request, *args, **kwargs):
        return redirect("basket:summary")

    def apply_voucher_to_basket(self, voucher):
        if voucher.is_expired():
            messages.error(
                self.request,
                _("The '%(code)s' voucher has expired") % {"code": voucher.code},
            )
            return

        if not voucher.is_active():
            messages.error(
                self.request,
                _("The '%(code)s' voucher is not active") % {"code": voucher.code},
            )
            return

        is_available, message = voucher.is_available_to_user(self.request.user)
        if not is_available:
            messages.error(self.request, message)
            return

        self.request.basket.vouchers.add(voucher)

        # Raise signal
        self.add_signal.send(sender=self, basket=self.request.basket, voucher=voucher)

        # Recalculate discounts to see if the voucher gives any
        Applicator().apply(self.request.basket, self.request.user, self.request)
        discounts_after = self.request.basket.offer_applications

        # Look for discounts from this new voucher
        found_discount = False
        for discount in discounts_after:
            if discount["voucher"] and discount["voucher"] == voucher:
                found_discount = True
                break
        if not found_discount:
            messages.warning(
                self.request, _("Your basket does not qualify for a voucher discount")
            )
            self.request.basket.vouchers.remove(voucher)
        else:
            messages.info(
                self.request,
                _("Voucher '%(code)s' added to basket") % {"code": voucher.code},
            )

    def form_valid(self, form):
        code = form.cleaned_data["code"]
        if not self.request.basket.id:
            return redirect_to_referrer(self.request, "basket:summary")
        if self.request.basket.contains_voucher(code):
            messages.error(
                self.request,
                _("You have already added the '%(code)s' voucher to your basket")
                % {"code": code},
            )
        else:
            try:
                voucher = self.voucher_model._default_manager.get(code=code)
            except self.voucher_model.DoesNotExist:
                messages.error(
                    self.request,
                    _("No voucher found with code '%(code)s'") % {"code": code},
                )
            else:
                self.apply_voucher_to_basket(voucher)
        return redirect_to_referrer(self.request, "basket:summary")

    def form_invalid(self, form):
        messages.error(self.request, _("Please enter a voucher code"))
        return redirect(reverse("basket:summary") + "#voucher")


class VoucherRemoveView(View):
    voucher_model = get_model("voucher", "voucher")
    remove_signal = voucher_removal
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        response = redirect("basket:summary")

        voucher_id = kwargs["pk"]
        if not request.basket.id:
            # Hacking attempt - the basket must be saved for it to have
            # a voucher in it.
            return response
        try:
            voucher = request.basket.vouchers.get(id=voucher_id)
        except ObjectDoesNotExist:
            messages.error(request, _("No voucher found with id '%s'") % voucher_id)
        else:
            request.basket.vouchers.remove(voucher)
            self.remove_signal.send(sender=self, basket=request.basket, voucher=voucher)
            messages.info(request, _("Voucher '%s' removed from basket") % voucher.code)

        return response




# =========
# Vlad try
# =========

class CheckoutView(OrderPlacementMixin, CheckoutSessionMixin,  generic.FormView):
   
    template_name = "oscar/checkout/form-all.html"
    template_name_preview = "oscar/checkout/preview.html"
    preview = True

    form_class = CheckoutForm
    success_url = reverse_lazy("checkout:thank-you")
    pre_conditions = [
        "check_basket_is_not_empty",
        "check_basket_is_valid",
        "check_user_email_is_captured",
    ]
    skip_conditions = ["skip_unless_basket_requires_shipping", "skip_unless_payment_is_required"]
    
    context_object_name = "order"


    def post(self, request, *args, **kwargs):

        # Posting to payment-details isn't the right thing to do.  Form
        # submissions should use the preview URL.
        if not self.preview:
            return http.HttpResponseBadRequest()

        self._methods = self.get_available_shipping_methods()

        super().post(request, *args, **kwargs)
        return self.handle_place_order_submission(request)












    #ok vrode
    def form_valid(self, form):
        # Store the address details in the session and redirect to next step
        address_fields = dict(
            (k, v) for (k, v) in form.instance.__dict__.items() if not k.startswith("_")
        )

        if self.request.user.is_authenticated and "address_id" in self.request.POST:
            address = UserAddress._default_manager.get(
                pk=self.request.POST["address_id"], user=self.request.user
            )
            self.checkout_session.ship_to_user_address(address)
        else:
            self.checkout_session.ship_to_new_address(address_fields)

        # Save the code for the chosen shipping method in the session
        # and continue to the next step.
        self.checkout_session.use_shipping_method(form.cleaned_data["method_code"])

        # Check that shipping address has been completed
        if not self.checkout_session.is_shipping_address_set():
            messages.error(self.request, _("Please choose a another shipping address"))
            return redirect("checkout:checkoutview")

    #ok - 1
    def get_skip_conditions(self, request):
        return super().get_skip_conditions(request)

    #ok - 2
    def get_pre_conditions(self, request):
        if self.preview:
            # The preview view needs to ensure payment information has been
            # correctly captured.
            return self.pre_conditions + ["check_payment_data_is_captured"]
        return super().get_pre_conditions(request)

    #ok 
    def get(self, request, *args, **kwargs):
        # These skip and pre conditions can't easily be factored out into the
        # normal pre-conditions as they do more than run a test and then raise
        # an exception on failure.

        # Check that shipping is required at all
        if not request.basket.is_shipping_required():
            # No shipping required - we store a special code to indicate so.
            self.checkout_session.use_shipping_method(NoShippingRequired().code)

        # Save shipping methods as instance var as we need them both here
        # and when setting the context vars.
        self._methods = self.get_available_shipping_methods()
        if len(self._methods) == 0:
            # No shipping methods available for given address
            messages.warning(
                request,
                _(
                    "Shipping is unavailable for your chosen address - please "
                    "choose another"
                ),
            )
            return redirect("checkout:checkoutview")
        elif len(self._methods) == 1:
            # Only one shipping method - set this and redirect onto the next
            # step
            self.checkout_session.use_shipping_method(self._methods[0].code)

        # Must be more than one available shipping method, we present them to
        # the user to make a choice.
        # By default we redirect straight onto the payment details view. Shops
        # that require a choice of payment method may want to override this
        # method to implement their specific logic.
        return super().get(request, *args, **kwargs)

    #ok - вызывается в 3
    def get_available_shipping_methods(self):
        """
        Returns all applicable shipping method objects for a given basket.
        """
        # Shipping methods can depend on the user, the contents of the basket
        # and the shipping address (so we pass all these things to the
        # repository).  I haven't come across a scenario that doesn't fit this
        # system.
        return Repository().get_shipping_methods(
            basket=self.request.basket,
            user=self.request.user,
            shipping_addr=self.get_shipping_address(self.request.basket),
            request=self.request,
        )

    #ok
    def get_initial(self):
        initial = self.checkout_session.new_shipping_address_fields()
        if initial:
            initial = initial.copy()
        return initial

    #ok
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["methods"] = self._methods
        return kwargs


    #ok
    def get_basket_voucher_form(self):
        """
        This is a separate method so that it's easy to e.g. not return a form
        if there are no vouchers available.
        """
        return BasketVoucherForm()
    
    #ok
    def get_context_data(self, **kwargs):

        #shipping address form
        ctx = super().get_context_data(**kwargs)
        #shipping method form
        ctx["methods"] = self._methods

        #promocode
        ctx["voucher_form"] = self.get_basket_voucher_form()

        if self.request.user.is_authenticated:
            # Look up address book data
            ctx["addresses"] = self.get_available_addresses()
        return ctx

    #ok
    def get_success_response(self):
        return redirect(self.get_success_url())

    #ok
    def get_available_addresses(self):
        # Include only addresses where the country is flagged as valid for
        # shipping. Also, use ordering to ensure the default address comes
        # first.
        return self.request.user.addresses.order_by("-is_default_for_shipping")

    #ok
    def form_invalid(self, form):
        messages.error(
            self.request, _("Your submitted shipping method is not permitted")
        )
        return super().form_invalid(form)

    #ok
    def get_success_url(self):
        return str(self.success_url)
    
    #ok
    def handle_place_order_submission(self, request):
        """
        Handle a request to place an order.

        This method is normally called after the customer has clicked "place
        order" on the preview page. It's responsible for (re-)validating any
        form information then building the submission dict to pass to the
        `submit` method.

        If forms are submitted on your payment details view, you should
        override this method to ensure they are valid before extracting their
        data into the submission dict and passing it onto `submit`.
        """
        return self.submit(**self.build_submission())

    #ok
    def handle_payment_details_submission(self, request):
        """
        Handle a request to submit payment details.

        This method will need to be overridden by projects that require forms
        to be submitted on the payment details view.  The new version of this
        method should validate the submitted form data and:

        - If the form data is valid, show the preview view with the forms
          re-rendered in the page
        - If the form data is invalid, show the payment details view with
          the form errors showing.

        """
        # No form data to validate by default, so we simply render the preview
        # page.  If validating form data and it's invalid, then call the
        # render_payment_details view.
        return self.render_preview(request)

    #ok
    def render_preview(self, request, **kwargs):
        """
        Show a preview of the order.

        If sensitive data was submitted on the payment details page, you will
        need to pass it back to the view here so it can be stored in hidden
        form inputs.  This avoids ever writing the sensitive data to disk.
        """
        self.preview = True
        ctx = self.get_context_data(**kwargs)
        return self.render_to_response(ctx)

    #ok
    def render_payment_details(self, request, **kwargs):
        """
        Show the payment details page

        This method is useful if the submission from the payment details view
        is invalid and needs to be re-rendered with form errors showing.
        """
        self.preview = False
        ctx = self.get_context_data(**kwargs)
        return self.render_to_response(ctx)

    #ne ok
    def submit(
        self,
        user,
        basket,
        shipping_address,
        shipping_method,
        shipping_charge,
        order_total,
        payment_kwargs=None,
        order_kwargs=None,
        surcharges=None,
    ):
        """
        Submit a basket for order placement.

        The process runs as follows:

         * Generate an order number
         * Freeze the basket so it cannot be modified any more (important when
           redirecting the user to another site for payment as it prevents the
           basket being manipulated during the payment process).
         * Attempt to take payment for the order
           - If payment is successful, place the order
           - If a redirect is required (e.g. PayPal, 3D Secure), redirect
           - If payment is unsuccessful, show an appropriate error message

        :basket: The basket to submit.
        :payment_kwargs: Additional kwargs to pass to the handle_payment
                         method. It normally makes sense to pass form
                         instances (rather than model instances) so that the
                         forms can be re-rendered correctly if payment fails.
        :order_kwargs: Additional kwargs to pass to the place_order method
        """
        if payment_kwargs is None:
            payment_kwargs = {}
        if order_kwargs is None:
            order_kwargs = {}

        # Taxes must be known at this point
        assert (
            basket.is_tax_known
        ), "Basket tax must be set before a user can place an order"
        assert (
            shipping_charge.is_tax_known
        ), "Shipping charge tax must be set before a user can place an order"

        # We generate the order number first as this will be used
        # in payment requests (ie before the order model has been
        # created).  We also save it in the session for multi-stage
        # checkouts (e.g. where we redirect to a 3rd party site and place
        # the order on a different request).
        order_number = self.generate_order_number(basket)
        self.checkout_session.set_order_number(order_number)
        logger.info(
            "Order #%s: beginning submission process for basket #%d",
            order_number,
            basket.id,
        )

        # Freeze the basket so it cannot be manipulated while the customer is
        # completing payment on a 3rd party site.  Also, store a reference to
        # the basket in the session so that we know which basket to thaw if we
        # get an unsuccessful payment response when redirecting to a 3rd party
        # site.
        self.freeze_basket(basket)
        self.checkout_session.set_submitted_basket(basket)

        # We define a general error message for when an unanticipated payment
        # error occurs.
        error_msg = _(
            "A problem occurred while processing payment for this "
            "order - no payment has been taken.  Please "
            "contact customer services if this problem persists"
        )

        signals.pre_payment.send_robust(sender=self, view=self)

        try:
            self.handle_payment(order_number, order_total, **payment_kwargs)
        except RedirectRequired as e:
            # Redirect required (e.g. PayPal, 3DS)
            logger.info("Order #%s: redirecting to %s", order_number, e.url)
            return http.HttpResponseRedirect(e.url)
        except UnableToTakePayment as e:
            # Something went wrong with payment but in an anticipated way.  Eg
            # their bankcard has expired, wrong card number - that kind of
            # thing. This type of exception is supposed to set a friendly error
            # message that makes sense to the customer.
            msg = str(e)
            logger.warning(
                "Order #%s: unable to take payment (%s) - restoring basket",
                order_number,
                msg,
            )
            self.restore_frozen_basket()

            # We assume that the details submitted on the payment details view
            # were invalid (e.g. expired bankcard).
            return self.render_payment_details(
                self.request, error=msg, **payment_kwargs
            )
        except PaymentError as e:
            # A general payment error - Something went wrong which wasn't
            # anticipated.  Eg, the payment gateway is down (it happens), your
            # credentials are wrong - that king of thing.
            # It makes sense to configure the checkout logger to
            # mail admins on an error as this issue warrants some further
            # investigation.
            msg = str(e)
            logger.error(
                "Order #%s: payment error (%s)", order_number, msg, exc_info=True
            )
            self.restore_frozen_basket()
            return self.render_preview(self.request, error=error_msg, **payment_kwargs)
        except Exception as e:
            # Unhandled exception - hopefully, you will only ever see this in
            # development...
            logger.exception(
                "Order #%s: unhandled exception while taking payment (%s)",
                order_number,
                e,
            )
            self.restore_frozen_basket()
            return self.render_preview(self.request, error=error_msg, **payment_kwargs)

        signals.post_payment.send_robust(sender=self, view=self)

        # If all is ok with payment, try and place order
        logger.info("Order #%s: payment successful, placing order", order_number)
        try:
            return self.handle_order_placement(
                order_number,
                user,
                basket,
                shipping_address,
                shipping_method,
                shipping_charge,
                order_total,
                surcharges=surcharges,
                **order_kwargs
            )
        except UnableToPlaceOrder as e:
            # It's possible that something will go wrong while trying to
            # actually place an order.  Not a good situation to be in as a
            # payment transaction may already have taken place, but needs
            # to be handled gracefully.
            msg = str(e)
            logger.error(
                "Order #%s: unable to place order - %s",
                order_number,
                msg,
                exc_info=True,
            )
            self.restore_frozen_basket()
            return self.render_preview(self.request, error=msg, **payment_kwargs)
        except Exception as e:
            # Hopefully you only ever reach this in development
            logger.exception(
                "Order #%s: unhandled exception while placing order (%s)",
                order_number,
                e,
            )
            error_msg = _(
                "A problem occurred while placing this order. Please contact customer services."
            )
            self.restore_frozen_basket()
            return self.render_preview(self.request, error=error_msg, **payment_kwargs)

    #ok
    # def get_template_names(self):
    #     return [self.template_name_preview] if self.preview else [self.template_name]
