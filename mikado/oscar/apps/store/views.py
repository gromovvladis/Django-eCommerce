# pylint: disable=attribute-defined-outside-init
from django import http
from django.conf import settings
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication


User = get_user_model()
Store = get_model("store", "Store")
StoreSelectForm = get_class("store.forms", "StoreSelectForm")

store_default = settings.STORE_DEFAULT

class StoreSelectModalView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]

    template_name = "oscar/store/store_modal.html"
    form_class = StoreSelectForm

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        store_modal_content = render_to_string(self.template_name, context, request=request)

        response = http.JsonResponse({
            "store_modal": store_modal_content,
        }, status=200)
        
        # Получаем данные о партнере из куки и корзины
        cookie_store = request.COOKIES.get('store')
        basket_store = getattr(request.basket, 'store_id', None)
        basket_store = str(basket_store) if basket_store is not None else None

        if basket_store and basket_store != cookie_store:
            # Устанавливаем партнера из корзины, если данные не совпадают с куки
            response.set_cookie("store", basket_store)
        elif not cookie_store and not basket_store:
            # Если данные о партнере отсутствуют в куки и корзине, устанавливаем по умолчанию
            response.set_cookie("store", store_default)

        # Возвращаем JSON-ответ с данными
        return response


    def get_context_data(self, *args, **kwargs):
        return {
            "store_form": self.get_store_form(*args, **kwargs)
        }

    def post(self, request, *args, **kwargs):
        form = self.form_class(self.request.POST)
        if form.is_valid():
            store_id = form.cleaned_data["store_id"]
            if request.basket:
                if request.basket.store_id != int(store_id):
                    request.basket.change_basket_store(store_id)
                    response = http.JsonResponse({"refresh": True, "status": 200}, status=200)
                else:
                    response = http.JsonResponse({"refresh": False, "status": 200}, status=200)
           
            response.set_cookie('store', store_id)
            return response

        return http.JsonResponse({"error": "Ошибка выбора магазина", "status": 400}, status=404)


    def get_store_form(self, *args, **kwargs):
        return self.form_class(**self.get_form_class_kwargs(*args, **kwargs))

    def get_form_class_kwargs(self, *args, **kwargs):
        store_id = self.request.basket.store_id or self.request.COOKIES.get('store_id') or store_default
        kwargs["initial"] = {
            "store_id": store_id,
        }
        return kwargs