# pylint: disable=attribute-defined-outside-init
from urllib.parse import unquote

from core.loading import get_class, get_classes, get_model
from django import http
from django.urls import reverse_lazy
from django.views import generic

PageTitleMixin, ThemeMixin = get_classes(
    "webshop.mixins", ["PageTitleMixin", "ThemeMixin"]
)
CheckoutSessionMixin = get_class("webshop.checkout.session", "CheckoutSessionMixin")
UserLiteAddressForm = get_class("webshop.address.forms", "UserLiteAddressForm")

UserAddress = get_model("address", "UserAddress")


class SetAddressView(PageTitleMixin, ThemeMixin, generic.CreateView):
    model = UserAddress
    form_class = UserLiteAddressForm
    template_name = "address/shipping-address.html"
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


class PickUpView(PageTitleMixin, ThemeMixin, generic.TemplateView):
    template_name = "address/pickup-address.html"
    page_title = "Самовывоз"
    context_object_name = "address"
