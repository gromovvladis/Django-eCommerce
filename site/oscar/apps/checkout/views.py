import datetime
import logging

from decimal import Decimal as D
from urllib.parse import unquote

from django import http
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views import generic
from django.template.loader import render_to_string
from django.views.generic import FormView, View
from django.core.exceptions import ObjectDoesNotExist

from oscar.core import prices
from oscar.core.loading import get_class, get_classes, get_model
from oscar.apps.basket.signals import voucher_addition, voucher_removal
from oscar.core.utils import redirect_to_referrer

from . import signals


Repository = get_class("shipping.repository", "Repository")
CheckoutForm = get_class("checkout.forms", "CheckoutForm")
RepositoryShipping = get_class("shipping.repository", "Repository")
UnableToPlaceOrder = get_class("order.exceptions", "UnableToPlaceOrder")
OrderPlacementMixin = get_class("checkout.mixins", "OrderPlacementMixin")
CheckoutSessionMixin = get_class("checkout.session", "CheckoutSessionMixin")
Applicator = get_class("offer.applicator", "Applicator")
CheckoutVoucherForm = get_class("checkout.forms", "CheckoutVoucherForm")
PaymentManager = get_class("payment.methods", "PaymentManager")
RedirectRequired, UnableToTakePayment, PaymentError = get_classes(
    "payment.exceptions", ["RedirectRequired", "UnableToTakePayment", "PaymentError"]
)

Source = get_model("payment", "Source")
SourceType = get_model("payment", "SourceType")
Order = get_model("order", "Order")
OrderNote = get_model("order", "OrderNote")

logger = logging.getLogger("oscar.checkout")


class IndexView(CheckoutSessionMixin, generic.FormView):
    """
    Check pre-cond and redirect to checkout
    """

    success_url = reverse_lazy("checkout:checkoutview")
    pre_conditions = [
        "delete_non_valid_lines",
        "check_basket_is_not_empty",
        "check_basket_is_valid",
    ]

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # We raise a signal to indicate that the user has entered the
            # checkout process so analytics tools can track this event.
            signals.start_checkout.send_robust(sender=self, request=request)
            return self.get_success_response()
        return redirect("basket:summary")

    def get_success_response(self):
        return redirect(self.get_success_url())


# =========
# Checkout
# =========


class CheckoutView(CheckoutSessionMixin, generic.FormView):
    template_name = "oscar/checkout/checkout_form.html"
    form_class = CheckoutForm
    success_url = reverse_lazy("checkout:payment-details")
    context_object_name = "order"
    pre_conditions = [
        "check_basket_is_not_empty",
        "check_basket_is_valid",
        "check_user_phone_is_captured",
    ]

    def get_initial(self):

        initial = {}
        if self.request.COOKIES.get("orderNote"):
            initial["order_note"] = unquote(
                unquote(self.request.COOKIES.get("orderNote"))
            )

        user_address = self.get_available_address()

        if user_address:
            initial["line1"] = user_address.line1
            initial["line2"] = user_address.line2
            initial["line3"] = user_address.line3
            initial["line4"] = user_address.line4
            initial["notes"] = user_address.notes
        else:
            if self.request.COOKIES.get("line1"):
                initial["line1"] = unquote(unquote(self.request.COOKIES.get("line1")))
            if self.request.COOKIES.get("line2"):
                initial["line2"] = unquote(unquote(self.request.COOKIES.get("line2")))
            if self.request.COOKIES.get("notes"):
                initial["line3"] = unquote(unquote(self.request.COOKIES.get("line3")))
            if self.request.COOKIES.get("line3"):
                initial["line4"] = unquote(unquote(self.request.COOKIES.get("line4")))
            if self.request.COOKIES.get("line4"):
                initial["notes"] = unquote(unquote(self.request.COOKIES.get("notes")))

        # initial['order_time'] = format(now() + datetime.timedelta(hours=2),'%d.%m.%Y %H:%M')
        initial["order_time"] = now() + datetime.timedelta(hours=2)

        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["methods"] = self._methods
        return kwargs

    def get_voucher_form(self):
        """
        This is a separate method so that it's easy to e.g. not return a form
        if there are no vouchers available.
        """
        return CheckoutVoucherForm()

    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)

        shipping_charge = prices.Price(
            currency=self.request.basket.currency, money=D("0.0")
        )
        min_order = prices.Price(
            currency=self.request.basket.currency, money=D("700.0")
        )

        method = self.get_default_shipping_method(self.request.basket)
        ctx["shipping_method"] = method

        # shipping method form
        if self.request.user.is_authenticated:
            # Look up address book data
            address = self.get_available_address()
            ctx["address"] = address
            if address and address.coords_lat and address.coords_long:
                shipping_charge, min_order = method.calculate(
                    self.request.basket, address
                )

        # payment form
        ctx["methods"] = self._methods
        ctx["min_order"] = int(min_order.money)
        ctx["shipping_charge"] = int(shipping_charge.money)

        # promocode
        ctx["voucher_form"] = self.get_voucher_form()

        return ctx

    def get_default_shipping_method(self, basket):
        return Repository().get_default_shipping_method(
            basket=self.request.basket,
            user=self.request.user,
            request=self.request,
        )

    def get_success_response(self):
        return redirect(self.get_success_url())

    def get_available_address(self):
        return getattr(self.request.user, "address", None)

    def get_available_shipping_methods(self):
        """
        Returns all applicable shipping method objects for a given basket.
        """
        # Shipping methods can depend on the user, the contents of the basket
        # and the shipping address (so we pass all these things to the
        # repository).  I haven't come across a scenario that doesn't fit this
        # system.
        return RepositoryShipping().get_shipping_methods(
            basket=self.request.basket,
            user=self.request.user,
            shipping_addr=self.get_shipping_address(self.request.basket),
            request=self.request,
        )

    def post(self, request, *args, **kwargs):
        self._methods = self.get_available_shipping_methods()
        super().post(request, *args, **kwargs)
        return redirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        self._methods = self.get_available_shipping_methods()
        if len(self._methods) == 0:
            # No shipping methods available for given address
            messages.warning(
                request,
                "Доставка недоступна по выбранному вами адресу — пожалуйста выберете другой адрес",
            )
            return redirect("checkout:checkoutview")

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):

        address_fields = dict(
            (k, v) for (k, v) in form.instance.__dict__.items() if not k.startswith("_")
        )
        shipping_method = form.cleaned_data["method_code"]

        # нужна проверак полей алреса
        if not self.is_shipping_address_set(address_fields, shipping_method):
            messages.error(self.request, "Введенный адрес некорректен")
            return redirect("checkout:checkoutview")

        # нужна проверка суммы минимального заказа при доставке
        if not self.is_min_order_set(form.instance, shipping_method):
            messages.error(self.request, "Сумма заказа меньше минимальной")
            return redirect("checkout:checkoutview")

        # нужна проверка корректности времени
        if not self.is_time_set(form.cleaned_data["order_time"]):
            messages.error(self.request, "Данное время заказа более не доступно")
            return redirect("checkout:checkoutview")

        # Store payment method in the CheckoutSessionMixin.checkout_session (a CheckoutSessionData object)
        self.checkout_session.set_session_address(address_fields)
        self.checkout_session.pay_by(form.cleaned_data["payment_method"])
        self.checkout_session.use_shipping_method(shipping_method)
        self.checkout_session.set_order_note(form.cleaned_data["order_note"])
        self.checkout_session.set_order_time(form.cleaned_data["order_time"])
        self.checkout_session.set_email_or_change(form.cleaned_data["email_or_change"])

    def is_shipping_address_set(self, address_fields, shipping_method):
        if shipping_method == "zona-shipping":
            requred_fields = [
                "line1",
                "line2",
                "line3",
                "line4",
                "coords_long",
                "coords_lat",
            ]
            for field in address_fields.items():
                if field[0] in requred_fields and not field[1]:
                    return False

        return True

    def is_min_order_set(self, shipping_address, shipping_method):
        if shipping_method == "zona-shipping":
            method = Repository().get_shipping_method(shipping_method)
            shipping_charge, min_order = method.calculate(
                self.request.basket, shipping_address
            )
            if min_order.money > self.request.basket.total:
                return False

        return True

    # переделай
    def is_time_set(self, order_time):
        return True

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Ошибка при оформлении заказа, пожалуйста, попробуйте еще раз.",
        )
        return super().form_invalid(form)

    def get_success_url(self):
        return str(self.success_url)


class PaymentDetailsView(OrderPlacementMixin, generic.TemplateView):
    """
    The final step to submit the payment.
    This includes an additional form to input comments, and proceeds to the payment provider.
    This connects to the django-oscar-docdata package to start the payment.
    For taking the details of payment and creating the order.

    This view class is used by two separate URLs: 'payment-details' and
    'preview'. The `preview` class attribute is used to distinguish which is
    being used. Chronologically, `payment-details` (preview=False) comes before
    `preview` (preview=True).

    If sensitive details are required (e.g. a bankcard), then the payment details
    view should submit to the preview URL and a custom implementation of
    `validate_payment_submission` should be provided.
    """

    template_name_preview = "oscar/checkout/preview.html"
    preview = False
    # If preview=True, then we render a preview template that shows all order
    # details ready for submission.
    # These conditions are extended at runtime depending on whether we are in
    # 'preview' mode or not.
    pre_conditions = [
        "check_basket_is_not_empty",
        "check_basket_is_valid",
        "check_shipping_data_is_captured",
        "check_payment_method_is_captured",  # переделай
        "check_order_time_is_captured",  # переделай
    ]

    def get(self, request, *args, **kwargs):
        return self.handle_place_order_submission(request)

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
        # Collect all the data!
        submission = self.build_submission()
        submission["payment_kwargs"]["submission"] = submission

        # Start the payment process!
        # This jumps to handle_payment()
        return self.submit(**submission)

    def submit(
        self,
        user,
        basket,
        shipping_address,
        shipping_method,
        shipping_charge,
        order_note,
        order_time,
        email_or_change,
        order_total,
        payment_kwargs=None,
        order_kwargs=None,
        surcharges=None,
    ):

        payment_method = self.checkout_session.payment_method()

        if payment_method is None:
            payment_method = "CASH"

        payment_kwargs["payment_method"] = payment_method

        if order_kwargs is None:
            order_kwargs = {}

        # We generate the order number first as this will be used
        # in payment requests (ie before the order model has been
        # created).  We also save it in the session for multi-stage
        # checkouts (e.g. where we redirect to a 3rd party site and place
        # the order on a different request).
        order_number = self.generate_order_number(basket)
        self.checkout_session.set_order_number(order_number)
        logger.info(
            "Заказ #%s: был подтвержен для корзины #%d",
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
        error_msg = (
            "Произошла проблема при обработке платежа. "
            "Оплата не была принята. "
            "Пожалуйста обратитесь в службу поддержки клиентов, если проблема не исчезнет"
        )

        try:
            source, order = self.add_source_and_create_order(
                order_number,
                user,
                basket,
                shipping_address,
                shipping_method,
                shipping_charge,
                order_total,
                payment_method,
                order_note,
                order_time,
                surcharges,
                **order_kwargs,
            )

        except UnableToPlaceOrder as e:
            # It's possible that something will go wrong while trying to
            # actually place an order.  Not a good situation to be in as a
            # payment transaction may already have taken place, but needs
            # to be handled gracefully.
            msg = str(e)
            logger.error(
                "Заказ #%s: невозможно разместить заказ - %s",
                order_number,
                msg,
                exc_info=True,
            )
            self.restore_frozen_basket()
            return self.render_preview(self.request, error=msg, **payment_kwargs)
        except Exception as e:
            # Hopefully you only ever reach this in development
            logger.exception(
                "Заказ #%s: ошибка во время размещения размещения заказа (%s)",
                order_number,
                e,
            )
            error_msg = "При размещении этого заказа возникла проблема. Пожалуйста, свяжитесь со службой поддержки клиентов."
            self.restore_frozen_basket()
            return self.render_preview(self.request, error=error_msg, **payment_kwargs)

        signals.pre_payment.send_robust(sender=self, view=self)

        try:
            self.handle_payment(
                order_total,
                source,
                order,
                payment_method,
                email_or_change,
                **payment_kwargs,
            )
        except RedirectRequired as e:
            # Redirect required (e.g. PayPal, 3DS)
            logger.info(
                "Заказ #%s: перенаправление на страницу оплаты %s", order_number, e.url
            )
            signals.post_payment.send_robust(sender=self, view=self, order=order)
            response = http.HttpResponseRedirect(e.url)
            cookies_to_delete = [
                "notes",
                "order_note",
                "line1",
                "line2",
                "line3",
                "line4",
            ]
            for cookie in cookies_to_delete:
                response.delete_cookie(cookie)
            return response
        except UnableToTakePayment as e:
            # Something went wrong with payment but in an anticipated way.  Eg
            # their bankcard has expired, wrong card number - that kind of
            # thing. This type of exception is supposed to set a friendly error
            # message that makes sense to the customer.
            msg = str(e)
            signals.error_order.send_robust(
                sender=self, error=e, order_number=order_number
            )
            logger.warning(
                "Заказ #%s: Невозможно произвести оплату (%s)",
                order_number,
                msg,
            )
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
            signals.error_order.send_robust(
                sender=self, error=e, order_number=order_number
            )
            logger.error(
                "Заказ #%s: ошибка оплаты (%s)", order_number, msg, exc_info=True
            )
            return self.render_preview(self.request, error=error_msg, **payment_kwargs)
        except Exception as e:
            # Unhandled exception - hopefully, you will only ever see this in
            # development...
            signals.error_order.send_robust(
                sender=self, error=e, order_number=order_number
            )
            logger.exception(
                "Заказ #%s: получил ошибку во время перехвата платежа (%s)",
                order_number,
                e,
            )
            return self.render_preview(self.request, error=error_msg, **payment_kwargs)

        signals.post_payment.send_robust(sender=self, view=self, order=order)
        return redirect("checkout:thank-you")

    def get_payment_method_display(self, payment_method):
        return dict(settings.WEBSHOP_PAYMENT_CHOICES).get(payment_method)

    def add_source_and_create_order(
        self,
        order_number,
        user,
        basket,
        shipping_address,
        shipping_method,
        shipping_charge,
        order_total,
        payment_method,
        order_note,
        order_time,
        surcharges,
        **order_kwargs,
    ):

        source = self._crete_source(payment_method, order_total)

        order = self._save_order(
            order_number,
            user,
            basket,
            shipping_address,
            shipping_method,
            shipping_charge,
            order_total,
            payment_method,
            order_time,
            surcharges,
            **order_kwargs,
        )

        if order_note:
            self._add_user_note(order, user, order_note)

        return source, order

    def _crete_source(self, payment_method, order_total):

        payment_name = self.get_payment_method_display(payment_method)

        source_type = SourceType.objects.get_or_create(name=payment_name)[0]

        source = Source(
            source_type=source_type,
            currency=order_total.currency,
            amount_allocated=order_total.money,
            reference=payment_method,
            refundable=False,
            paid=False,
        )

        self.add_payment_source(source)

        return source

    def _save_order(
        self,
        order_number,
        user,
        basket,
        shipping_address,
        shipping_method,
        shipping_charge,
        order_total,
        payment_method,
        order_time,
        surcharges,
        **order_kwargs,
    ):
        # Finalize the order that PaymentDetailsView.submit() started
        # If all is ok with payment, try and place order
        logger.info("Заказ #%s: оплата началась, идет размещение заказа", order_number)

        if payment_method in settings.ONLINE_PAYMENTS:
            order_kwargs["status"] = settings.OSCAR_INITIAL_ONLINE_PAYMENT_ORDER_STATUS
        else:
            order_kwargs["status"] = settings.OSCAR_INITIAL_ORDER_STATUS

        try:
            return self.handle_order_placement(
                order_number=order_number,
                user=user,
                basket=basket,
                shipping_address=shipping_address,
                shipping_method=shipping_method,
                shipping_charge=shipping_charge,
                order_total=order_total,
                order_time=order_time,
                surcharges=surcharges,
                **order_kwargs,
            )
        except UnableToPlaceOrder as e:
            # It's possible that something will go wrong while trying to
            # actually place an order.  Not a good situation to be in as a
            # payment transaction may already have taken place, but needs
            # to be handled gracefully.
            logger.error(
                "Заказ #%s: неудалось разместить заказ - %s",
                order_number,
                e,
                exc_info=True,
            )
            signals.error_order.send_robust(
                sender=self, error=e, order_number=order_number
            )
            self.restore_frozen_basket()
            return self.render_to_response(self.get_context_data(error=e))

    def _add_user_note(self, order, user, order_note):
        try:
            note = OrderNote(
                order=order,
                user=user,
                note_type="Комментарий к заказу",
                message=order_note,
            )
            note.save()
        except ObjectDoesNotExist:
            pass

    def normalize_email(self, email):
        email = email or ""
        try:
            email_name, domain_part = email.strip().rsplit("@", 1)
        except ValueError:
            pass
        else:
            email = email_name + "@" + domain_part.lower()
        return email

    def handle_payment(
        self, total, source, order, source_reference, email_or_change, **kwargs
    ):
        payment_method = PaymentManager(source_reference).get_method()
        email = ""

        if source_reference in settings.CASH_PAYMENTS and email_or_change:
            self.add_payment_event(
                "Требуется сдача",
                int(email_or_change),
            )
            self.save_payment_events(order)
        else:
            email = self.normalize_email(email_or_change)

        payment = payment_method.pay(
            order=order,
            source=source,
            amount=total,
            email=email,
        )

        if email:
            order.user.email = email
            order.user.save()

        if payment is not None:
            self.save_payment_events(order)

            url = payment.confirmation.confirmation_url
            logger.info("Redirecting user to {0}".format(url))
            raise RedirectRequired(url)

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

    def render_payment_details(self, request, **kwargs):
        """
        Show the payment details page

        This method is useful if the submission from the payment details view
        is invalid and needs to be re-rendered with form errors showing.
        """
        self.preview = False
        ctx = self.get_context_data(**kwargs)
        return self.render_to_response(ctx)

    def get_template_names(self):
        return [self.template_name_preview] if self.preview else [self.template_name]


class UpdateTotalsView(View):
    def get(self, request, *args, **kwargs):
        try:
            new_method = request.GET.get("shipping_method")
            zona_id = request.GET.get("zona_id")
            shipping_method = self.get_shipping_method(new_method)
            shipping_charge, min_order = shipping_method.calculate(
                self.request.basket, zona_id
            )
            min_order_html = (
                "Минимальная сумма заказа для доставки %s ₽" % min_order.money
            )

            new_totals = render_to_string(
                "oscar/checkout/checkout_totals.html",
                {
                    "basket": self.request.basket,
                    "shipping_method": shipping_method,
                    "shipping_charge": shipping_charge,
                    "min_order": min_order,
                },
                request=self.request,
            )
            return http.JsonResponse(
                {"totals": new_totals, "min_order": min_order_html, "status": 202},
                status=202,
            )
        except Exception:
            return http.JsonResponse({"totals": "error", "status": 200}, status=200)

    def get_shipping_method(self, new_method):
        return Repository().get_shipping_method(method=new_method)


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
        pk = ctx["order"].pk
        key = "order_{}_thankyou_viewed".format(pk)
        if not self.request.session.get(key, False):
            self.request.session[key] = True
            ctx["send_analytics_event"] = True
        else:
            ctx["send_analytics_event"] = False

        return ctx


# =========
# Voucher
# =========


def update_discounts(basket, user, request):
    basket.reset_offer_applications()
    Applicator().apply(basket, user, request)
    return basket.offer_applications


class VoucherAddView(FormView):
    form_class = CheckoutVoucherForm
    voucher_model = get_model("voucher", "voucher")
    add_signal = voucher_addition

    def get(self, request, *args, **kwargs):
        return redirect("checkout:checkoutview")

    def apply_voucher_to_basket(self, voucher, _dict):
        if voucher.is_expired():
            _dict["message"] = ("Срок действия промокода '{0}' истек").format(
                voucher.code
            )
            return _dict, 200

        if not voucher.is_active():
            _dict["message"] = ("Промокод '{0}' не активен").format(voucher.code)
            return _dict, 200

        is_available, message = voucher.is_available_to_user(self.request.user)
        if not is_available:
            _dict["message"] = message
            return _dict, 200

        self.request.basket.vouchers.add(voucher)

        # Raise signal
        self.add_signal.send(sender=self, basket=self.request.basket, voucher=voucher)

        discounts_after = update_discounts(
            self.request.basket, self.request.user, self.request
        )

        found_discount = False
        for discount in discounts_after:
            if discount["voucher"] and discount["voucher"] == voucher:
                found_discount = True
                break
        if not found_discount:
            self.request.basket.vouchers.remove(voucher)
            _dict["message"] = (
                "На вашу корзину не распространяется скидка по промокоду."
            )
            return _dict, 200

        else:
            _dict["message"] = "Промокод '%(code)s' успешно применен!" % {
                "code": voucher.code
            }
            _dict["new_totals"] = render_to_string(
                "oscar/checkout/checkout_totals.html",
                {"basket": self.request.basket, "editable": True},
                request=self.request,
            )
            return _dict, 202

    def form_valid(self, form):
        code = form.cleaned_data["code"]
        _dict = {}
        status = 200
        if not self.request.basket.id:
            return redirect_to_referrer(self.request, "checkout:checkoutview")
        if self.request.basket.contains_voucher(code):
            _dict["message"] = ("Промокод '{0}' уже применен").format(code)
        else:
            try:
                voucher = self.voucher_model._default_manager.get(code=code)
            except self.voucher_model.DoesNotExist:
                _dict["message"] = (("Промокод '{0}' не найден").format(code),)
            else:
                _dict, status = self.apply_voucher_to_basket(voucher, _dict)

        return http.JsonResponse(_dict, status=status)

    def form_invalid(self, form):
        return redirect(reverse("basket:summary") + "#voucher")


class VoucherRemoveView(View):
    voucher_model = get_model("voucher", "voucher")
    remove_signal = voucher_removal
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        status = 200
        _dict = {}
        voucher_id = kwargs["pk"]
        if not request.basket.id:
            # Hacking attempt - the basket must be saved for it to have
            # a voucher in it.
            return redirect("checkout:checkoutview")
        try:
            voucher = request.basket.vouchers.get(id=voucher_id)
        except ObjectDoesNotExist:
            _dict["message"] = "Промокод с кодом '%s' не найден" % voucher_id
        else:
            request.basket.vouchers.remove(voucher)
            self.remove_signal.send(sender=self, basket=request.basket, voucher=voucher)
            update_discounts(request.basket, request.user, request)
            new_totals = render_to_string(
                "oscar/checkout/checkout_totals.html",
                {"basket": request.basket},
                request=request,
            )
            _dict = {
                "message": "Промокд '%s' успешно удален" % voucher.code,
                "new_totals": new_totals,
            }
            status = 202

        _dict["status"] = status
        return http.JsonResponse(_dict, status=status)
