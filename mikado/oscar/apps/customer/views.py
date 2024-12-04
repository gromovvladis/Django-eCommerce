# pylint: disable=attribute-defined-outside-init
from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic

from oscar.apps.customer.mixins import RegisterUserPhoneMixin
from oscar.apps.customer.utils import get_password_reset_url
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_classes, get_model
from django.template.loader import render_to_string
from oscar.views.generic import PostActionMixin
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication

import sys
sys.path.append(".")

from apps.sms_auth.providers.base import Smsaero
from apps.sms_auth.services import GeneratorService

from . import signals

PageTitleMixin, RegisterUserMixin = get_classes(
    "customer.mixins", ["PageTitleMixin", "RegisterUserMixin"]
)
CustomerDispatcher = get_class("customer.utils", "CustomerDispatcher")
PhoneAuthenticationForm, OrderSearchForm = get_classes(
    "customer.forms",
    ["PhoneAuthenticationForm", "OrderSearchForm"],
)
ProfileForm = get_class("customer.forms", "ProfileForm")
UserAddressForm = get_class("address.forms", "UserAddressForm")
Order = get_model("order", "Order")
UserAddress = get_model("address", "UserAddress")

User = get_user_model()


# =======
# Account
# =======


class AccountSummaryView(generic.RedirectView):
    """
    View that exists for legacy reasons and customisability. It commonly gets
    called when the user clicks on "Account" in the navbar.

    Oscar defaults to just redirecting to the profile summary page (and
    that redirect can be configured via OSCAR_ACCOUNT_REDIRECT_URL), but
    it's also likely you want to display an 'account overview' page or
    such like. The presence of this view allows just that, without
    having to change a lot of templates.
    """

    pattern_name = settings.OSCAR_ACCOUNTS_REDIRECT_URL
    permanent = False
 

class AccountAuthModalView(RegisterUserPhoneMixin, APIView):
    """
    Resiter via sms.
    """
    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]

    template_name = "oscar/customer/auth_modal.html"
    form_class = PhoneAuthenticationForm
    redirect_field_name = "next"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        context = self.get_context_data()
        auth_modal = render_to_string(self.template_name, context, request=request)
        return http.JsonResponse({"auth_modal": auth_modal}, status = 202)


    def get_context_data(self, *args, **kwargs):
        return {
            "auth_form": self.get_auth_form()
        }


    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == "sms":
            return self.validate_sms_form()
        if request.POST.get('action') == "auth":
            return self.validate_auth_form()
        return http.JsonResponse({"errors": "Ошибка авторизации", "status": 400}, status=400)


    # AUTH
    def get_auth_form(self, bind_data=False):
        return self.form_class(**self.get_auth_form_kwargs(bind_data))


    def get_auth_form_kwargs(self, bind_data=False):
        kwargs = {}
        kwargs["request"] = self.request
        kwargs["host"] = self.request.get_host()
        kwargs["initial"] = {
            "username": self.request.POST.get("username"),
        }
        if bind_data and self.request.method in ("POST", "PUT"):
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )
        return kwargs


    def validate_auth_form(self):
        form = self.get_auth_form(bind_data=True)
        if form.is_valid():
            
            user = form.get_user()

            if user is not None:
                # Grab a reference to the session ID before logging in
                old_session_key = self.request.session.session_key
                auth_login(self.request, user, backend="apps.user.auth_backends.PhoneBackend")
                # Raise signal robustly (we don't want exceptions to crash the
                # request handling). We use a custom signal as we want to track the
                # session key before calling login (which cycles the session ID).
                signals.user_logged_in.send_robust(
                    sender=self,
                    request=self.request,
                    user=user,
                    old_session_key=old_session_key,
                )

                url = self.get_auth_success_url(form)

                return http.JsonResponse({"success": url, "status": 200}, status=200)

        return http.JsonResponse({"error": "Код не верный", "status": 400}, status=404)


    def get_auth_success_url(self, form):    
        redirect_url = self.request.POST.get('redirect_url')
        if redirect_url:
            return redirect_url
        
        return settings.LOGIN_REDIRECT_URL


    def validate_sms_form(self):
        form = self.get_auth_form(bind_data=True)
        if form.is_valid():
            try:
                phone = form.get_phone()

                sms_generator = GeneratorService(phone)
                
                sms_code = sms_generator.process()
                sms_message = sms_code.message

                auth_service = Smsaero(phone, sms_message)
                sms_result = auth_service.send_sms()

                if sms_result == 'secceded':
                    return http.JsonResponse({"secceded": "Смс выслано", "status": 200}, status=200)

            except Exception as e:
                return http.JsonResponse({"error": e.message, "status": 403}, status=403)

        return http.JsonResponse({"error": "Укажите корректный номер телефона", "status": 400}, status=400)
    

class AccountAuthView(generic.TemplateView, AccountAuthModalView):
    """
    Resiter via sms.
    """
    template_name = "oscar/customer/auth.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["auth_form"] = self.get_auth_form()
        return ctx


class LogoutView(generic.RedirectView):
    url = settings.OSCAR_HOMEPAGE
    permanent = False

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        response = super().get(request, *args, **kwargs)

        for cookie in settings.OSCAR_COOKIES_DELETE_ON_LOGOUT:
            response.delete_cookie(cookie)

        return response


# =============
# Profile
# =============


class ProfileView(PageTitleMixin, generic.UpdateView):
    form_class = ProfileForm
    template_name = "oscar/customer/profile/profile_form.html"
    page_title = "Профиль"
    active_tab = "profile"
    model = User
    context_object_name = 'user'
    success_url = reverse_lazy("customer:profile-view")

    def get_object(self):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["summary"] = "Профиль"
        ctx["content_open"] = False
        return ctx

    
    def get_initial(self):
        return {
            "name": self.request.user.name,
            "email": self.request.user.email,
        }

    def form_valid(self, form):
        # Grab current user instance before we save form. We may need this to
        # send a warning email if the email address is changed.
        try: 
            old_user = User.objects.get(id=self.request.user.id)
        except User.DoesNotExist:
            old_user = None

        form.save()

        # We have to look up the email address from the form's
        # cleaned data because the object created by form.save() can
        # either be a user or profile instance depending whether a profile
        # class has been specified by the AUTH_PROFILE_MODULE setting.
        new_email = form.cleaned_data.get("email")
        if new_email and old_user and new_email != old_user.email:
            # Email address has changed - send a confirmation email to the old
            # address including a password reset link in case this is a
            # suspicious change.
            old_user.is_email_verified = False
            self.send_email_changed_email(old_user, new_email)

        return http.JsonResponse({"message": "Информация успешно обновлена"}, status=200)

    def form_invalid(self, form):
        return http.JsonResponse({"message":", ".join(form.errors)}, status=402)

    def send_email_changed_email(self, old_user, new_email):
        user = self.request.user
        extra_context = {
            "user": user,
            "reset_url": get_password_reset_url(old_user),
            "new_email": new_email,
            "request": self.request,
        }
        CustomerDispatcher().send_email_changed_email_for_user(old_user, extra_context)


# =============
# Order history
# =============


class OrderHistoryView(PageTitleMixin, generic.ListView):
    """
    Customer order history
    """

    context_object_name = "orders"
    template_name = "oscar/customer/order/order_list.html"
    paginate_by = settings.OSCAR_ORDERS_PER_PAGE
    model = Order
    form_class = OrderSearchForm
    page_title = "История заказов"
    active_tab = "orders"

    def get(self, request, *args, **kwargs):
        if "date_range" in request.GET:
            self.form = self.form_class(self.request.GET)
            if not self.form.is_valid():
                self.object_list = self.get_queryset()
                ctx = self.get_context_data(object_list=self.object_list)
                return self.render_to_response(ctx)
            data = self.form.cleaned_data

            # If the user has just entered an order number, try and look it up
            # and redirect immediately to the order detail page.
            if data["order_number"] and not data["date_range"]:
                try:
                    order = Order.objects.get(
                        number=data["order_number"], user=self.request.user
                    )
                except Order.DoesNotExist:
                    pass
                else:
                    return redirect("customer:order", order_number=order.number)
        else:
            self.form = self.form_class()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return Queryset of :py:class:`Order <oscar.apps.order.models.Order>`
        instances for the currently authenticated user.
        """
        qs = self.model._default_manager.filter(user=self.request.user)
        if self.form.is_bound and self.form.is_valid():
            qs = qs.filter(**self.form.get_filters())
        return qs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["form"] = self.form
        ctx["content_open"] = True
        ctx["summary"] = "Профиль"
        return ctx


class OrderDetailView(PageTitleMixin, PostActionMixin, generic.DetailView):
    model = Order
    active_tab = "orders"

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["summary"] = "Профиль"
        ctx["content_open"] = True
        ctx["online_payments"] = settings.ONLINE_PAYMENTS
        return ctx

    def get_template_names(self):
        return ["oscar/customer/order/order_detail.html"]

    def get_page_title(self):
        """
        Order number as page title
        """
        return "%s №%s" % ("Заказ", self.object.number)

    def get_object(self, queryset=None):
        dfbdfb = get_object_or_404(
            self.model, user=self.request.user, number=self.kwargs["order_number"]
        )
        return get_object_or_404(
            self.model, user=self.request.user, number=self.kwargs["order_number"]
        )

    def do_reorder(self, order):
        """
        'Re-order' a previous order.

        This puts the contents of the previous order into your basket
        """
        # Collect lines to be added to the basket and any warnings for lines
        # that are no longer available.
        basket = self.request.basket
        lines_to_add = []
        warnings = []
        for line in order.lines.all():
            is_available, reason = line.is_available_to_reorder(
                basket, self.request.strategy
            )
            if is_available:
                lines_to_add.append(line)
            else:
                warnings.append(reason)

        # Check whether the number of items in the basket won't exceed the
        # maximum.
        total_quantity = sum([line.quantity for line in lines_to_add])
        is_quantity_allowed, reason = basket.is_quantity_allowed(total_quantity)
        if not is_quantity_allowed:
            messages.warning(self.request, reason)
            self.response = redirect("customer:order-list")
            return

        # Add any warnings
        for warning in warnings:
            messages.warning(self.request, warning)

        for line in lines_to_add:
            additionals = []
            options = []
            for attribute in line.attributes.all():
                if attribute.option:
                    options.append(
                        {"option": attribute.option, "value": attribute.value}
                    )
                else:   
                    additionals.append(
                        {"additional": attribute.additional, "value": attribute.value}
                    )
            basket.add_product(line.product, line.quantity, options, additionals)

        if len(lines_to_add) > 0:
            self.response = redirect("basket:summary")
        else:
            self.response = redirect("customer:order-list")


# class OrderLineView(PostActionMixin, generic.DetailView):
#     """Customer order line"""

#     def get_object(self, queryset=None):
#         order = get_object_or_404(
#             Order, user=self.request.user, number=self.kwargs["order_number"]
#         )
#         return order.lines.get(id=self.kwargs["line_id"])

#     def do_reorder(self, line):
#         self.response = redirect("customer:order", self.kwargs["order_number"])
#         basket = self.request.basket

#         line_available_to_reorder, reason = line.is_available_to_reorder(
#             basket, self.request.strategy
#         )

#         if not line_available_to_reorder:
#             messages.warning(self.request, reason)
#             return

#         # We need to pass response to the get_or_create... method
#         # as a new basket might need to be created
#         self.response = redirect("basket:summary")

#         # Convert line attributes into basket options
#         options = []
#         for attribute in line.attributes.all():
#             if attribute.option:
#                 options.append({"option": attribute.option, "value": attribute.value})
#         basket.add_product(line.product, line.quantity, options)

#         if line.quantity > 1:
#             msg = "%(qty)d шт. - '%(product)s' были добавлены в вашу корзину" % {"qty": line.quantity, "product": line.product}
#         else:
#             msg = "'%s' добавлен в вашу корзину" % line.product

#         messages.info(self.request, msg)


# ------------
# Address book
# ------------


class AddressListView(PageTitleMixin, generic.ListView):
    """Customer address book"""

    context_object_name = "addresses"
    template_name = "oscar/customer/address/address_list.html"
    paginate_by = settings.OSCAR_ADDRESSES_PER_PAGE
    active_tab = "addresses"
    page_title = "Адрес доставки"

    def get_queryset(self):
        """Return customer's addresses"""
        return UserAddress._default_manager.filter(user=self.request.user)
    
    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["content_open"] = True
        ctx["summary"] = "Профиль"
        return ctx


class AddressCreateView(PageTitleMixin, generic.CreateView):
    form_class = UserAddressForm
    model = UserAddress
    template_name = "oscar/customer/address/address_form.html"
    active_tab = "addresses"
    page_title = "Добавить новый адрес"
    success_url = reverse_lazy("customer:address-list")

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Добавить новый адрес"
        ctx["summary"] = "Профиль"
        ctx["content_open"] = True
        return ctx

    def get_success_url(self):
        # messages.success(self.request, _("Address '%s' created") % self.object.summary)
        return super().get_success_url()


class AddressUpdateView(PageTitleMixin, generic.UpdateView):
    form_class = UserAddressForm
    model = UserAddress
    template_name = "oscar/customer/address/address_form.html"
    active_tab = "addresses"
    page_title = "Изменить адрес"
    success_url = reverse_lazy("customer:address-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Изменить адрес"
        ctx["summary"] = "Профиль"
        ctx["content_open"] = True
        return ctx

    def get_queryset(self):
        return self.request.user.addresses.all()

    def get_success_url(self):
        return super().get_success_url()


class AddressDeleteView(PageTitleMixin, generic.DeleteView):
    model = UserAddress
    template_name = "oscar/customer/address/address_delete.html"
    page_title = "Удалить адрес?"
    active_tab = "addresses"
    context_object_name = "address"
    success_url = reverse_lazy("customer:address-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Удалить адрес"
        ctx["summary"] = "Профиль"
        ctx["content_open"] = True
        return ctx

    def get_queryset(self):
        return UserAddress._default_manager.filter(user=self.request.user)

    def get_success_url(self):
        messages.success(self.request, "Адрес '%s' удален" % self.object.summary)
        return super().get_success_url()
