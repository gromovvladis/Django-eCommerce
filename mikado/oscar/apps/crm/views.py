import json
from django.conf import settings
from django.http import JsonResponse

from oscar.apps.crm.client import EvatorCloud
from oscar.apps.telegram.models import TelegramMessage
from oscar.core.loading import get_model
from oscar.apps.telegram.bot.synchron.send_message import send_message_to_staffs


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


import logging

logger = logging.getLogger("oscar.crm")

CRMEvent = get_model("crm", "CRMEvent")
Store = get_model("store", "Store")

site_token = settings.EVOTOR_SITE_TOKEN
user_token = settings.EVOTOR_SITE_USER_TOKEN

site_login = settings.EVOTOR_SITE_LOGIN
site_pass = settings.EVOTOR_SITE_PASS


# ========= вспомогательные функции =========


def is_valid_site_token(request):
    # Проверка токена сайта
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response(
            {"errors": [{"code": 1001}]}, status=status.HTTP_401_UNAUTHORIZED
        )

    auth_token = auth_header.split(" ")[1]
    if not auth_header or auth_token != site_token:
        return Response(
            {"errors": [{"code": 1001}]}, status=status.HTTP_401_UNAUTHORIZED
        )

    return None  # Если все проверки прошли, возвращаем None


def is_valid_user_token(request):
    # Проверка токена сайта
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response(
            {"errors": [{"code": 1001}]}, status=status.HTTP_401_UNAUTHORIZED
        )

    auth_token = auth_header.split(" ")[1]
    if not auth_header or auth_token != user_token:
        return Response(
            {"errors": [{"code": 1001}]}, status=status.HTTP_401_UNAUTHORIZED
        )

    return None  # Если все проверки прошли, возвращаем None


def is_valid_user_login_and_pass(request):
    # Получение данных пользователя
    user_data = request.data
    login = user_data.get("login")
    password = user_data.get("password")

    if not login or not password or login != site_login or password != site_pass:
        return Response(
            {"errors": [{"code": 1006}]}, status=status.HTTP_401_UNAUTHORIZED
        )

    return None  # Если все проверки прошли, возвращаем None


def is_valid_site_and_user_tokens(request):
    return is_valid_site_token(request) or is_valid_user_login_and_pass(request)


# ========= API Endpoints (Уведомления) =========

# сериализаторы
#  1. Магазин и терминалы +
#  2. персонал +

#  3. товар
#  3.1 категории и варианты товаров (схемы и модификации)

#  4. заказ

# новые модели
#  1. чек
#  2. документ
#  3. событие +

# добавь испльзование курсора, если объектов много


class CRMInstallationEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/subscription/setup """

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }
        logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
        send_message_to_staffs(
            f"request: {json.dumps(request_info, ensure_ascii=False)}",
            TelegramMessage.TECHNICAL,
        )

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        CRMEvent.objects.create(
            body=f"Terminals recived {request.data}",
            sender=CRMEvent.INSTALLATION,
            type=CRMEvent.INFO,
        )
        return JsonResponse({"status": "success"}, status=200)


class CRMLoginEndpointView(APIView):
    """https://mikado-sushi.ru/crm/api/user/login"""

    authentication_classes = []
    permission_classes = [AllowAny]

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request):

        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }
        logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
        send_message_to_staffs(
            f"request: {json.dumps(request_info, ensure_ascii=False)}",
            TelegramMessage.TECHNICAL,
        )

        not_allowed = is_valid_site_and_user_tokens(request)
        if not_allowed:
            return not_allowed

        return Response(
            {"userId": request.data.get("userId"), "token": user_token},
            status=status.HTTP_200_OK,
        )


class CRMStoreEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/stores """

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        stores_json = request.data.get("items")

        stores = []
        for store_json in stores_json:
            stores.append(store_json.get("id", "Магазин"))

        CRMEvent.objects.create(
            body=f"Добавлены или изменены магазины: {', '.join(stores)}",
            sender=CRMEvent.STORE,
            type=CRMEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_stores(stores_json)

        return JsonResponse({"status": "ok"}, status=200)


class CRMTerminalEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/terminals """

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }
        logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
        send_message_to_staffs(
            f"request: {json.dumps(request_info, ensure_ascii=False)}",
            TelegramMessage.TECHNICAL,
        )

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        terminals_json = request.data.get("items")

        terminals = []
        for terminal_json in terminals_json:
            terminals.append(terminal_json.get("id", "Терминал"))

        CRMEvent.objects.create(
            body=f"Добавлены или изменены терминалы: {', '.join(terminals)}",
            sender=CRMEvent.TERMINAL,
            type=CRMEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_terminals(terminals_json)

        return JsonResponse({"status": "ok"}, status=200)


class CRMStaffEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/staffs """

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        staffs_json = request.data.get("items")

        staffs = []
        for staff_json in staffs_json:
            staffs.append(staff_json.get("id", "Сотрудник"))

        CRMEvent.objects.create(
            body=f"Добавлены или изменены сотрудники: {', '.join(staffs)}",
            sender=CRMEvent.STAFF,
            type=CRMEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_staffs(staffs_json)

        return JsonResponse({"status": "ok"}, status=200)


class CRMRoleEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/roles """

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        roles_json = request.data.get("items")

        roles = []
        for role_json in roles_json:
            roles.append(role_json.get("id", "Роль сотрудников"))

        CRMEvent.objects.create(
            body=f"Добавлены или изменены роли сотрудников: {', '.join(roles)}",
            sender=CRMEvent.STAFF,
            type=CRMEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_roles(roles_json)

        return JsonResponse({"status": "ok"}, status=200)


class CRMProductEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/stores/<str:store_id>/products/ """

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }
        logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
        send_message_to_staffs(
            f"request: {json.dumps(request_info, ensure_ascii=False)}",
            TelegramMessage.TECHNICAL,
        )

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        products_json = request.data
        for product in products_json:
            product["id"] = product.pop("uuid", None)
            product["parent_id"] = product.pop("parentUuid", None)
            product["store_id"] = kwargs["store_id"]

        products = []
        for product_json in products_json:
            products.append(product_json.get("id", "Продукт"))

        CRMEvent.objects.create(
            body=f"Добавлены или изменены продукты: {', '.join(products)}",
            sender=CRMEvent.PRODUCT,
            type=CRMEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_products(products_json)

        return JsonResponse({"status": "success"}, status=200)


class CRMDocsEndpointView(APIView):

    permission_classes = [AllowAny]

    """ 
    https://mikado-sushi.ru/crm/api/docs 

    1. Продажа (SELL)
    2. Возврат (PAYBACK)
    3. Приемка (ACCEPT)
    4. Списание (WRITE_OFF)
    5. Инвентаризация (INVENTORY)
    6. Переоценка (REVALUATION)
    7. Внесение наличных (CASH_INCOME)
    8. Изъятие наличных (CASH_OUTCOME)
    """

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }
        logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
        send_message_to_staffs(
            f"request: {json.dumps(request_info, ensure_ascii=False)}",
            TelegramMessage.TECHNICAL,
        )

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        request_type = request.data.get("type")

        if request_type == "SELL":
            self.sell(request.data, *args, **kwargs)
        elif request_type == "PAYBACK":
            self.payback(request.data, *args, **kwargs)
        elif request_type == "ACCEPT":
            self.accept(request.data, *args, **kwargs)
        elif request_type == "WRITE_OFF":
            self.write_off(request.data, *args, **kwargs)
        elif request_type == "INVENTORY":
            self.inventory(request.data, *args, **kwargs)
        elif request_type == "REVALUATION":
            self.revaluation(request.data, *args, **kwargs)
        elif request_type == "CASH_INCOME":
            self.cash_income(request.data, *args, **kwargs)
        elif request_type == "CASH_OUTCOME":
            self.cash_outcome(request.data, *args, **kwargs)
        else:
            CRMEvent.objects.create(
                body="Error: Неподдерживаемый тип документа.",
                sender=CRMEvent.DOC,
                type=CRMEvent.ERROR,
            )

        return JsonResponse({"status": "success"}, status=200)

    def sell(self, data):

        CRMEvent.objects.create(
            body=f"Добавлен офлайн заказ: { data.get('id', 'Заказ') }",
            sender=CRMEvent.ORDER,
            type=CRMEvent.CREATION,
        )

        EvatorCloud().create_or_update_site_order(data)

    def payback(self, data):
        pass

    def accept(self, data):
        pass

    def write_off(self, data):
        pass

    def inventory(self, data):
        pass

    def revaluation(self, data):
        pass

    def cash_income(self, data):
        pass

    def cash_outcome(self, data):
        pass
