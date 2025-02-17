# pylint: disable=attribute-defined-outside-init
from urllib.parse import unquote

from django import http
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.views import generic

from oscar.core.loading import get_class, get_model

PageTitleMixin = get_class("customer.mixins", "PageTitleMixin")
CheckoutSessionMixin = get_class("checkout.session", "CheckoutSessionMixin")
UserLiteAddressForm = get_class("address.forms", "UserLiteAddressForm")

UserAddress = get_model("address", "UserAddress")


class SetAddressView(PageTitleMixin, generic.CreateView):

    form_class = UserLiteAddressForm
    model = UserAddress
    template_name = "oscar/address/delivery-address.html"
    active_tab = "address"
    page_title = "Добавить адрес"
    context_object_name = "address"
    success_url = reverse_lazy("customer:address-list")

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().post(request, *args, **kwargs)
        return http.JsonResponse({"saved": "cookies"}, status=200)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return TemplateResponse(
            request, self.template_name, {self.context_object_name: context}
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = {}
        context["title"] = "Добавить новый адрес"
        context["readonly"] = False
        user_address = False
        if self.request.user.is_authenticated:
            user_address = self.request.user.address
        if user_address:
            context["line1"] = user_address.line1
            context["readonly"] = True
        elif self.request.COOKIES.get("line1"):
            context["line1"] = unquote(unquote(self.request.COOKIES.get("line1")))
            context["readonly"] = True
        return context

    def get_success_url(self):
        return super().get_success_url()


class PickUpView(generic.View):
    template_name = "oscar/address/pickup-address.html"
    page_title = "Самовывоз"
    context_object_name = "address"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return TemplateResponse(
            request, self.template_name, {self.context_object_name: context}
        )

    def get_context_data(self, **kwargs):
        context = {}
        context["title"] = "Самовывоз"
        return context
