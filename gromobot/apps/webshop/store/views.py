# pylint: disable=attribute-defined-outside-init
from core.compat import get_user_model
from core.loading import get_class, get_model
from django import http
from django.conf import settings
from django.template.loader import render_to_string
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

StoreSelectForm = get_class("webshop.store.forms", "StoreSelectForm")
ThemeMixin = get_class("webshop.mixins", "ThemeMixin")

User = get_user_model()
Store = get_model("store", "Store")

store_default = settings.STORE_DEFAULT


class StoreSelectModalView(ThemeMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]
    template_name = "store/store_modal.html"
    form_class = StoreSelectForm

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        store_modal_content = render_to_string(
            self.template_name, context, request=request
        )

        response = http.JsonResponse(
            {
                "store_modal": store_modal_content,
            },
            status=200,
        )

        self.set_store_cookie_from_basket_or_cookie(request, response)
        return response

    def post(self, request, *args, **kwargs):
        form = self.form_class(self.request.POST)
        if form.is_valid():
            form_store_id = form.cleaned_data["store_id"]
            basket_store_id = request.store.id

            if basket_store_id and basket_store_id != int(form_store_id):
                request.basket.change_basket_store(form_store_id)
                response = http.JsonResponse({"refresh": True}, status=200)
            else:
                response = http.JsonResponse({"refresh": False}, status=200)

            # Устанавливаем куки с выбранным магазином
            self.set_store_cookie(response, form_store_id)
            return response

        return http.JsonResponse({"error": "Ошибка выбора магазина"}, status=404)

    def get_context_data(self, *args, **kwargs):
        return {"store_form": self.get_store_form(*args, **kwargs)}

    def get_store_form(self, *args, **kwargs):
        return self.form_class(**self.get_form_class_kwargs(*args, **kwargs))

    def get_form_class_kwargs(self, *args, **kwargs):
        kwargs["initial"] = {
            "store_id": self.request.store.id,
        }
        return kwargs

    def set_store_cookie(self, response, store_id):
        response.set_cookie("store", store_id, max_age=settings.STORE_COOKIE_LIFETIME)

    def set_store_cookie_from_basket_or_cookie(self, request, response):
        cookie_store = request.COOKIES.get("store")
        basket_store = getattr(request.basket, "store_id", None)

        if basket_store and str(basket_store) != cookie_store:
            # Если данные не совпадают, устанавливаем куки из корзины
            self.set_store_cookie(response, basket_store)
        elif not cookie_store and not basket_store:
            # Если нет данных в корзине и куках, устанавливаем по умолчанию
            self.set_store_cookie(response, store_default)
