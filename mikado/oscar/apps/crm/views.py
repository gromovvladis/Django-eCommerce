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

        request = {
            "method": "PUT",
            "path": "/crm/api/docs/",
            "headers": {
                "Host": "mikado-sushi.ru",
                "X-Real-Ip": "185.170.204.77",
                "X-Forwarded-For": "185.170.204.77",
                "Connection": "close",
                "Content-Length": "2318",
                "Accept": "application/json, application/*+json",
                "Content-Type": "application/json",
                "Authorization": "Bearer 9179d780-56a4-49ea-b042-435e3257eaf8",
                "X-Evotor-User-Id": "01-000000010409029",
                "X-B3-Traceid": "50fa3b712d25cff7",
                "X-B3-Spanid": "823eb830f325361a",
                "X-B3-Parentspanid": "50fa3b712d25cff7",
                "X-B3-Sampled": "0",
                "User-Agent": "Java/1.8.0_151",
            },
            "data": {
                "type": "SELL",
                "id": "1163c91a-c96d-4176-ae1e-c51b05d2f43d",
                "extras": {},
                "number": 30532,
                "close_date": "2024-12-04T05:18:33.000+0000",
                "time_zone_offset": 25200000,
                "session_id": "e83777cb-8cd5-4ae2-9cfa-c63313469cf0",
                "session_number": 148,
                "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
                "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
                "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
                "user_id": "01-000000010409029",
                "body": {
                    "positions": [
                        {
                            "product_id": "7927d7af-57fb-4282-8d73-fc763a4a32ee",
                            "quantity": 1,
                            "initial_quantity": -9,
                            "quantity_in_package": null,
                            "bar_code": null,
                            "product_type": "NORMAL",
                            "mark": null,
                            "mark_data": null,
                            "alcohol_by_volume": 0,
                            "alcohol_product_kind_code": 0,
                            "tare_volume": 0,
                            "code": "61",
                            "product_name": "Какао 0,4",
                            "measure_name": "шт",
                            "id": 235572,
                            "uuid": "bc161751-e530-43e5-a96a-70a4ed4e8734",
                            "extra_keys": [],
                            "sub_positions": [],
                            "measure_precision": 0,
                            "price": 290,
                            "cost_price": 0,
                            "result_price": 290,
                            "sum": 290,
                            "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
                            "result_sum": 290,
                            "position_discount": null,
                            "doc_distributed_discount": null,
                            "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                            "splitted_positions": null,
                            "attributes_choices": null,
                            "settlement_method": {
                                "type": "CHECKOUT_FULL",
                                "amount": null,
                            },
                            "agent_requisites": null,
                        }
                    ],
                    "doc_discounts": [],
                    "payments": [
                        {
                            "id": "aa79bfde-c7da-4e9b-940b-52f1f319f5b0",
                            "parent_id": null,
                            "sum": 1000,
                            "type": "CASH",
                            "parts": [
                                {
                                    "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                                    "part_sum": 1000,
                                    "change": 710,
                                }
                            ],
                            "app_payment": null,
                            "merchant_info": null,
                            "bank_info": null,
                            "app_info": {"app_id": null, "name": "Наличные"},
                        }
                    ],
                    "print_groups": [
                        {
                            "id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                            "type": "CASH_RECEIPT",
                            "org_name": null,
                            "org_inn": null,
                            "org_address": null,
                            "taxation_system": null,
                            "medicine_attributes": null,
                        }
                    ],
                    "pos_print_results": [
                        {
                            "receipt_number": 8577,
                            "document_number": 9138,
                            "session_number": 147,
                            "receipt_date": "04122024",
                            "receipt_time": "1218",
                            "fn_reg_number": null,
                            "fiscal_sign_doc_number": "2980820727",
                            "fiscal_document_number": 29960,
                            "fn_serial_number": "7382440700036332",
                            "kkt_serial_number": "00307900652283",
                            "kkt_reg_number": "0008200608019020",
                            "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                            "check_sum": 290,
                        }
                    ],
                    "sum": 290,
                    "result_sum": 290,
                    "customer_email": null,
                    "customer_phone": null,
                },
                "counterparties": null,
                "created_at": "2024-12-04T05:18:35.649+0000",
                "version": "V2",
            },
        }

        request = {
            "method": "PUT",
            "path": "/crm/api/docs/",
            "headers": {
                "Host": "mikado-sushi.ru",
                "X-Real-Ip": "185.170.204.77",
                "X-Forwarded-For": "185.170.204.77",
                "Connection": "close",
                "Content-Length": "2591",
                "Accept": "application/json, application/*+json",
                "Content-Type": "application/json",
                "Authorization": "Bearer 9179d780-56a4-49ea-b042-435e3257eaf8",
                "X-Evotor-User-Id": "01-000000010409029",
                "X-B3-Traceid": "b735f46e6dea712d",
                "X-B3-Spanid": "0c7b0bf5c32980db",
                "X-B3-Parentspanid": "b735f46e6dea712d",
                "X-B3-Sampled": "0",
                "User-Agent": "Java/1.8.0_151",
            },
            "data": {
                "type": "SELL",
                "id": "c1200ed4-4b28-4ca5-9ee7-fc6326729d9a",
                "extras": {},
                "number": 30536,
                "close_date": "2024-12-04T05:26:56.000+0000",
                "time_zone_offset": 25200000,
                "session_id": "e83777cb-8cd5-4ae2-9cfa-c63313469cf0",
                "session_number": 148,
                "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
                "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
                "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
                "user_id": "01-000000010409029",
                "body": {
                    "positions": [
                        {
                            "product_id": "13111c38-e846-41f7-a723-7914a818eaac",
                            "quantity": 1,
                            "initial_quantity": -445,
                            "quantity_in_package": null,
                            "bar_code": null,
                            "product_type": "NORMAL",
                            "mark": null,
                            "mark_data": null,
                            "alcohol_by_volume": 0,
                            "alcohol_product_kind_code": 0,
                            "tare_volume": 0,
                            "code": "2",
                            "product_name": "Кофе 0,3",
                            "measure_name": "шт",
                            "id": 235615,
                            "uuid": "ff71c388-9805-4e3d-9506-635853f5f59d",
                            "extra_keys": [],
                            "sub_positions": [],
                            "measure_precision": 0,
                            "price": 280,
                            "cost_price": 0,
                            "result_price": 140,
                            "sum": 280,
                            "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
                            "result_sum": 140,
                            "position_discount": null,
                            "doc_distributed_discount": {
                                "discount_sum": 140,
                                "discount_percent": 50,
                                "discount_type": "SUM",
                                "coupon": null,
                                "discount_price": null,
                            },
                            "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                            "splitted_positions": null,
                            "attributes_choices": null,
                            "settlement_method": {
                                "type": "CHECKOUT_FULL",
                                "amount": null,
                            },
                            "agent_requisites": null,
                        }
                    ],
                    "doc_discounts": [
                        {
                            "discount_sum": 140,
                            "discount_percent": 50,
                            "discount_type": "SUM",
                            "coupon": null,
                        }
                    ],
                    "payments": [
                        {
                            "id": "4236bfb1-796d-4c90-ac98-bbd3ccf3c52c",
                            "parent_id": null,
                            "sum": 140,
                            "type": "ELECTRON",
                            "parts": [
                                {
                                    "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                                    "part_sum": 140,
                                    "change": 0,
                                }
                            ],
                            "app_payment": null,
                            "merchant_info": {
                                "number": "123",
                                "english_name": "123",
                                "category_code": "123",
                            },
                            "bank_info": {"name": "ПАО СБЕРБАНК"},
                            "app_info": {"app_id": null, "name": "Банковская карта"},
                        }
                    ],
                    "print_groups": [
                        {
                            "id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                            "type": "CASH_RECEIPT",
                            "org_name": null,
                            "org_inn": null,
                            "org_address": null,
                            "taxation_system": null,
                            "medicine_attributes": null,
                        }
                    ],
                    "pos_print_results": [
                        {
                            "receipt_number": 8581,
                            "document_number": 9142,
                            "session_number": 147,
                            "receipt_date": "04122024",
                            "receipt_time": "1226",
                            "fn_reg_number": null,
                            "fiscal_sign_doc_number": "2066966750",
                            "fiscal_document_number": 29964,
                            "fn_serial_number": "7382440700036332",
                            "kkt_serial_number": "00307900652283",
                            "kkt_reg_number": "0008200608019020",
                            "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                            "check_sum": 140,
                        }
                    ],
                    "sum": 280,
                    "result_sum": 140,
                    "customer_email": null,
                    "customer_phone": null,
                },
                "counterparties": null,
                "created_at": "2024-12-04T05:26:58.992+0000",
                "version": "V2",
            },
        }

        request = {
            "method": "PUT",
            "path": "/crm/api/docs/",
            "headers": {
                "Host": "mikado-sushi.ru",
                "X-Real-Ip": "185.170.204.77",
                "X-Forwarded-For": "185.170.204.77",
                "Connection": "close",
                "Content-Length": "3933",
                "Accept": "application/json, application/*+json",
                "Content-Type": "application/json",
                "Authorization": "Bearer 9179d780-56a4-49ea-b042-435e3257eaf8",
                "X-Evotor-User-Id": "01-000000010409029",
                "X-B3-Traceid": "c0fb39c7835f7454",
                "X-B3-Spanid": "2b32f935476aedd9",
                "X-B3-Parentspanid": "c0fb39c7835f7454",
                "X-B3-Sampled": "0",
                "User-Agent": "Java/1.8.0_151",
            },
            "data": {
                "type": "SELL",
                "id": "1ce80c10-09d1-4e74-8c17-76f5b0f646ed",
                "extras": {},
                "number": 30556,
                "close_date": "2024-12-04T06:09:27.000+0000",
                "time_zone_offset": 25200000,
                "session_id": "e83777cb-8cd5-4ae2-9cfa-c63313469cf0",
                "session_number": 148,
                "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
                "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
                "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
                "user_id": "01-000000010409029",
                "body": {
                    "positions": [
                        {
                            "product_id": "797f6172-96f6-4eb3-ad3f-9f3e7042e580",
                            "quantity": 3,
                            "initial_quantity": -452,
                            "quantity_in_package": null,
                            "bar_code": null,
                            "product_type": "NORMAL",
                            "mark": null,
                            "mark_data": null,
                            "alcohol_by_volume": 0,
                            "alcohol_product_kind_code": 0,
                            "tare_volume": 0,
                            "code": "9",
                            "product_name": "Торт",
                            "measure_name": "шт",
                            "id": 235792,
                            "uuid": "ee15f9d4-ba0d-4308-8c6f-f4cb5b7e8e6d",
                            "extra_keys": [],
                            "sub_positions": [],
                            "measure_precision": 0,
                            "price": 350,
                            "cost_price": 0,
                            "result_price": 350,
                            "sum": 1050,
                            "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
                            "result_sum": 1050,
                            "position_discount": null,
                            "doc_distributed_discount": null,
                            "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                            "splitted_positions": null,
                            "attributes_choices": null,
                            "settlement_method": {
                                "type": "CHECKOUT_FULL",
                                "amount": null,
                            },
                            "agent_requisites": null,
                        },
                        {
                            "product_id": "13111c38-e846-41f7-a723-7914a818eaac",
                            "quantity": 1,
                            "initial_quantity": -451,
                            "quantity_in_package": null,
                            "bar_code": null,
                            "product_type": "NORMAL",
                            "mark": null,
                            "mark_data": null,
                            "alcohol_by_volume": 0,
                            "alcohol_product_kind_code": 0,
                            "tare_volume": 0,
                            "code": "2",
                            "product_name": "Кофе 0,3",
                            "measure_name": "шт",
                            "id": 235794,
                            "uuid": "852e1ad2-cb99-412c-878e-fc7c694f6e62",
                            "extra_keys": [],
                            "sub_positions": [],
                            "measure_precision": 0,
                            "price": 280,
                            "cost_price": 0,
                            "result_price": 280,
                            "sum": 280,
                            "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
                            "result_sum": 280,
                            "position_discount": null,
                            "doc_distributed_discount": null,
                            "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                            "splitted_positions": null,
                            "attributes_choices": null,
                            "settlement_method": {
                                "type": "CHECKOUT_FULL",
                                "amount": null,
                            },
                            "agent_requisites": null,
                        },
                        {
                            "product_id": "c9f60c6f-b133-4f7e-b187-ee87406cdfba",
                            "quantity": 1,
                            "initial_quantity": -75,
                            "quantity_in_package": null,
                            "bar_code": null,
                            "product_type": "NORMAL",
                            "mark": null,
                            "mark_data": null,
                            "alcohol_by_volume": 0,
                            "alcohol_product_kind_code": 0,
                            "tare_volume": 0,
                            "code": "29",
                            "product_name": "Чай авторский",
                            "measure_name": "шт",
                            "id": 235796,
                            "uuid": "5ff1ab0a-16a3-4d58-b40d-b192df927edb",
                            "extra_keys": [],
                            "sub_positions": [],
                            "measure_precision": 0,
                            "price": 390,
                            "cost_price": 0,
                            "result_price": 390,
                            "sum": 390,
                            "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
                            "result_sum": 390,
                            "position_discount": null,
                            "doc_distributed_discount": null,
                            "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                            "splitted_positions": null,
                            "attributes_choices": null,
                            "settlement_method": {
                                "type": "CHECKOUT_FULL",
                                "amount": null,
                            },
                            "agent_requisites": null,
                        },
                    ],
                    "doc_discounts": [],
                    "payments": [
                        {
                            "id": "e51feb7a-143a-4c21-a500-eb89856ef33d",
                            "parent_id": null,
                            "sum": 5000,
                            "type": "CASH",
                            "parts": [
                                {
                                    "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                                    "part_sum": 5000,
                                    "change": 3280,
                                }
                            ],
                            "app_payment": null,
                            "merchant_info": null,
                            "bank_info": null,
                            "app_info": {"app_id": null, "name": "Наличные"},
                        }
                    ],
                    "print_groups": [
                        {
                            "id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                            "type": "CASH_RECEIPT",
                            "org_name": null,
                            "org_inn": null,
                            "org_address": null,
                            "taxation_system": null,
                            "medicine_attributes": null,
                        }
                    ],
                    "pos_print_results": [
                        {
                            "receipt_number": 8601,
                            "document_number": 9164,
                            "session_number": 147,
                            "receipt_date": "04122024",
                            "receipt_time": "1309",
                            "fn_reg_number": null,
                            "fiscal_sign_doc_number": "419560768",
                            "fiscal_document_number": 29984,
                            "fn_serial_number": "7382440700036332",
                            "kkt_serial_number": "00307900652283",
                            "kkt_reg_number": "0008200608019020",
                            "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
                            "check_sum": 1720,
                        }
                    ],
                    "sum": 1720,
                    "result_sum": 1720,
                    "customer_email": null,
                    "customer_phone": null,
                },
                "counterparties": null,
                "created_at": "2024-12-04T06:09:29.221+0000",
                "version": "V2",
            },
        }

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
