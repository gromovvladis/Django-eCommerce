from urllib.parse import unquote
from django import http
from django.urls import reverse_lazy
from django.views import generic
from core.loading import get_class, get_classes, get_model

PageTitleMixin, ThemeMixin = get_classes(
    "webshop.mixins", ["PageTitleMixin", "ThemeMixin"]
)
UserLiteAddressForm = get_class("webshop.address.forms", "UserLiteAddressForm")
UserAddress = get_model("address", "UserAddress")


class BaseAddressView(PageTitleMixin, ThemeMixin):
    """Базовый класс для views работы с адресами"""

    context_object_name = "address"

    def get_user_address(self):
        """Получает адрес пользователя, если он аутентифицирован"""
        if self.request.user.is_authenticated:
            return getattr(self.request.user, "address", None)
        return None


class SetAddressView(BaseAddressView, generic.CreateView):
    model = UserAddress
    form_class = UserLiteAddressForm
    template_name = "address/shipping-address.html"
    page_title = "Добавить адрес"
    success_url = reverse_lazy("customer:address-list")

    def post(self, request, *args, **kwargs):
        """Обработка POST запроса"""
        if not request.user.is_authenticated:
            return http.JsonResponse({"saved": "cookies"}, status=200)
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Добавляем пользователя в kwargs формы"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Добавляем данные адреса в контекст"""
        context = super().get_context_data(**kwargs)
        context["readonly"] = False

        # Получаем адрес из разных источников
        if user_address := self.get_user_address():
            context["line1"] = user_address.line1
            context["readonly"] = True
        elif line1 := self.request.COOKIES.get("line1"):
            context["line1"] = unquote(unquote(line1))
            context["readonly"] = True

        return context


class PickUpView(BaseAddressView, generic.TemplateView):
    template_name = "address/pickup-address.html"
    page_title = "Самовывоз"
