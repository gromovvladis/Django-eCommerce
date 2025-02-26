# pylint: disable=attribute-defined-outside-init
from urllib.parse import unquote

from django import http
from django.urls import reverse_lazy
from django.views import generic

from oscar.core.loading import get_class, get_model

PageTitleMixin = get_class("customer.mixins", "PageTitleMixin")
CheckoutSessionMixin = get_class("checkout.session", "CheckoutSessionMixin")
UserLiteAddressForm = get_class("address.forms", "UserLiteAddressForm")

UserAddress = get_model("address", "UserAddress")


class SetAddressView(PageTitleMixin, generic.CreateView):
    model = UserAddress
    form_class = UserLiteAddressForm
    template_name = "oscar/address/delivery-address.html"
    page_title = "Добавить адрес"
    context_object_name = "address"
    success_url = reverse_lazy("customer:address-list")

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().post(request, *args, **kwargs)
        return http.JsonResponse({"saved": "cookies"}, status=200)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["readonly"] = False
        user_address = False
        if self.request.user.is_authenticated:
            user_address = getattr(self.request.user, "address", None)
        if user_address:
            context["line1"] = user_address.line1
            context["readonly"] = True
        elif self.request.COOKIES.get("line1"):
            context["line1"] = unquote(unquote(self.request.COOKIES.get("line1")))
            context["readonly"] = True
        return context


class PickUpView(PageTitleMixin, generic.TemplateView):
    template_name = "oscar/address/pickup-address.html"
    page_title = "Самовывоз"
    context_object_name = "address"
