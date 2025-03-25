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
        templates = self.get_template_names()
        store_modal_content = render_to_string(templates[0], context, request=request)

        response = http.JsonResponse(
            {
                "store_modal": store_modal_content,
            },
            status=200,
        )

        # Получаем данные о партнере из куки и корзины
        cookie_store = request.COOKIES.get("store")
        basket_store = getattr(request.basket, "store_id", None)
        basket_store = str(basket_store) if basket_store is not None else None

        if basket_store and basket_store != cookie_store:
            # Устанавливаем партнера из корзины, если данные не совпадают с куки
            response.set_cookie(
                "store", basket_store, max_age=settings.STORE_COOKIE_LIFETIME
            )
        elif not cookie_store and not basket_store:
            # Если данные о партнере отсутствуют в куки и корзине, устанавливаем по умолчанию
            response.set_cookie(
                "store", store_default, max_age=settings.STORE_COOKIE_LIFETIME
            )

        # Возвращаем JSON-ответ с данными
        return response

    def get_context_data(self, *args, **kwargs):
        return {"store_form": self.get_store_form(*args, **kwargs)}

    def post(self, request, *args, **kwargs):
        form = self.form_class(self.request.POST)
        if form.is_valid():
            form_store_id = form.cleaned_data["store_id"]
            request_store_id = request.store.id
            if request_store_id:
                if request_store_id != int(form_store_id):
                    request.basket.change_basket_store(form_store_id)
                    response = http.JsonResponse(
                        {"refresh": True, "status": 200}, status=200
                    )
                else:
                    response = http.JsonResponse(
                        {"refresh": False, "status": 200}, status=200
                    )

            response.set_cookie(
                "store", form_store_id, max_age=settings.STORE_COOKIE_LIFETIME
            )
            return response

        return http.JsonResponse(
            {"error": "Ошибка выбора магазина", "status": 400}, status=404
        )

    def get_store_form(self, *args, **kwargs):
        return self.form_class(**self.get_form_class_kwargs(*args, **kwargs))

    def get_form_class_kwargs(self, *args, **kwargs):
        kwargs["initial"] = {
            "store_id": self.request.store.id,
        }
        return kwargs
