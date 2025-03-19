import json
import logging

from django.conf import settings
from django.http import JsonResponse
from apps.evotor.api.cloud import EvatorCloud
from apps.telegram.bot.synchron.send_message import send_message_to_staffs
from apps.telegram.models import TelegramMessage
from core.loading import get_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

EvotorEvent = get_model("evotor", "EvotorEvent")
Store = get_model("store", "Store")

logger = logging.getLogger("apps.evotor")

site_token = settings.EVOTOR_SITE_TOKEN
user_token = settings.EVOTOR_SITE_USER_TOKEN

site_login = settings.EVOTOR_SITE_LOGIN
site_pass = settings.EVOTOR_SITE_PASS

# ========= вспомогательные функции =========


def is_valid_site_token(request):
    # Проверка токена сайта
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.error(f"Токен авторизации сайта отсутствует. Токен: {auth_header}")
        return Response(
            {"errors": [{"code": 1001}]}, status=status.HTTP_401_UNAUTHORIZED
        )

    auth_token = auth_header.split(" ")[1]
    if not auth_header or auth_token != site_token:
        logger.error(f"Токен авторизации сайта не верный. Токен: {auth_header}")
        return Response(
            {"errors": [{"code": 1001}]}, status=status.HTTP_401_UNAUTHORIZED
        )

    return None  # Если все проверки прошли, возвращаем None


def is_valid_user_token(request):
    # Проверка токена сайта
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.error(f"Токен пользователя отсутствует. Токен: {auth_header}")
        return Response(
            {"errors": [{"code": 1001}]}, status=status.HTTP_401_UNAUTHORIZED
        )

    auth_token = auth_header.split(" ")[1]
    if not auth_header or auth_token != user_token:
        logger.error(f"Токен пользователя не верный. Токен: {auth_header}")
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
        logger.error(f"Неверный пароль или логин. Логин: {login}, Пароль:{password}")
        return Response(
            {"errors": [{"code": 1006}]}, status=status.HTTP_401_UNAUTHORIZED
        )

    return None  # Если все проверки прошли, возвращаем None


def is_valid_site_and_user_tokens(request):
    return is_valid_site_token(request) or is_valid_user_login_and_pass(request)


# ========= API Endpoints (Уведомления) =========
# добавь испльзование курсора, если объектов много


class EvotorInstallationEndpointView(APIView):
    """https://site.ru/evotor/api/subscription/setup"""

    permission_classes = [AllowAny]

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

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        EvotorEvent.objects.create(
            body=f"Приложение установлено {request.data}",
            sender=EvotorEvent.INSTALLATION,
            event_type=EvotorEvent.INFO,
        )
        return JsonResponse({"status": "success"}, status=200)


class EvotorLoginEndpointView(APIView):
    """https://site.ru/evotor/api/user/login"""

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

        not_allowed = is_valid_site_and_user_tokens(request)
        if not_allowed:
            return not_allowed

        return Response(
            {"userId": request.data.get("userId"), "token": user_token},
            status=status.HTTP_200_OK,
        )


class EvotorStoreEndpointView(APIView):
    """https://site.ru/evotor/api/stores"""

    permission_classes = [AllowAny]

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        stores_json = request.data.get("items")

        stores = []
        for store_json in stores_json:
            stores.append(store_json.get("name", "Магазин"))

        EvotorEvent.objects.create(
            body=f"Добавлены или изменены магазины: {', '.join(stores)}",
            sender=EvotorEvent.STORE,
            event_type=EvotorEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_stores(stores_json)

        return JsonResponse({"status": "ok"}, status=200)


class EvotorTerminalEndpointView(APIView):
    """https://site.ru/evotor/api/terminals"""

    permission_classes = [AllowAny]

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

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        terminals_json = request.data.get("items")

        terminals = []
        for terminal_json in terminals_json:
            terminals.append(terminal_json.get("id", "Терминал"))

        EvotorEvent.objects.create(
            body=f"Добавлены или изменены терминалы: {', '.join(terminals)}",
            sender=EvotorEvent.TERMINAL,
            event_type=EvotorEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_terminals(terminals_json)

        return JsonResponse({"status": "ok"}, status=200)


class EvotorStaffEndpointView(APIView):
    """https://site.ru/evotor/api/staffs"""

    permission_classes = [AllowAny]

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        staffs_json = request.data.get("items")

        staffs = []
        for staff_json in staffs_json:
            staffs.append(
                ", ".join(
                    staff_json.get("name", "Имя сотрудника"),
                    staff_json.get("last_name", "Фамилия сотрудника"),
                )
            )

        EvotorEvent.objects.create(
            body=f"Добавлены или изменены сотрудники: {', '.join(staffs)}",
            sender=EvotorEvent.STAFF,
            event_type=EvotorEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_staffs(staffs_json)

        return JsonResponse({"status": "ok"}, status=200)


class EvotorRoleEndpointView(APIView):
    """https://site.ru/evotor/api/roles"""

    permission_classes = [AllowAny]

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        roles_json = request.data.get("items")

        roles = []
        for role_json in roles_json:
            roles.append(role_json.get("name", "Роль сотрудников"))

        EvotorEvent.objects.create(
            body=f"Добавлены или изменены роли сотрудников: {', '.join(roles)}",
            sender=EvotorEvent.STAFF,
            event_type=EvotorEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_roles(roles_json)

        return JsonResponse({"status": "ok"}, status=200)


class EvotorProductEndpointView(APIView):
    """https://site.ru/evotor/api/stores/<str:store_id>/products/"""

    permission_classes = [AllowAny]

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
            products.append(product_json.get("name", "Товар без имени"))

        EvotorEvent.objects.create(
            body=f"Добавлены или изменены товары: {', '.join(products)}",
            sender=EvotorEvent.PRODUCT,
            event_type=EvotorEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_products(products_json)

        return JsonResponse({"status": "success"}, status=200)


class EvotorDocsEndpointView(APIView):
    """
    https://site.ru/evotor/api/docs

    1. Продажа (SELL) +
    2. Возврат (PAYBACK) +
    3. Коррекция (CORRECTION) +

    4. Приемка (ACCEPT) +
    5. Списание (WRITE_OFF) +
    6. Инвентаризация (INVENTORY) +

    7. Переоценка (REVALUATION)

    8. Внесение наличных (CASH_INCOME) +
    9. Изъятие наличных (CASH_OUTCOME) +
    """

    permission_classes = [AllowAny]

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        request_type = request.data.get("type")

        if request_type != "SELL":
            send_message_to_staffs(
                f"request: {json.dumps(request_info, ensure_ascii=False)}",
                TelegramMessage.TECHNICAL,
            )

        if request_type in ["SELL", "CORRECTION"]:
            self.sell(request.data, *args, **kwargs)
        elif request_type == "PAYBACK":
            self.payback(request.data, *args, **kwargs)
        elif request_type in ["ACCEPT", "WRITE_OFF", "INVENTORY"]:
            self.stockrecord_operation(request.data, *args, **kwargs)
        elif request_type in ["CASH_INCOME", "CASH_OUTCOME"]:
            self.cash_transaction(request.data, *args, **kwargs)
        elif request_type == "REVALUATION":
            self.revaluation(request.data, *args, **kwargs)
        else:
            EvotorEvent.objects.create(
                body="Error: Неподдерживаемый тип документа.",
                sender=EvotorEvent.DOC,
                event_type=EvotorEvent.ERROR,
            )

        return JsonResponse({"status": "success"}, status=200)

    def sell(self, data):
        EvatorCloud().create_or_update_site_order(data)

    def payback(self, data):
        EvatorCloud().refund_site_order(data)

    def stockrecord_operation(self, data):
        EvatorCloud().stockrecord_operation(data)

    def cash_transaction(self, data):
        EvatorCloud().cash_transaction(data)

    def revaluation(self, data):
        pass


# {
#     "type": "SELL",
#     "id": "81f72cae-11b6-465b-be75-03b64bd1d58b",
#     "extras": {},
#     "number": 50247,
#     "close_date": "2025-02-23T05:36:45.000+0000",
#     "time_zone_offset": 25200000,
#     "session_id": "e16daae2-567f-4718-84cf-dbf9f973ab1c",
#     "session_number": 229,
#     "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
#     "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
#     "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
#     "user_id": "01-000000010409029",
#     "body": {
#         "positions": [
#             {
#                 "product_id": "7ae0a004-45b3-40fb-985f-6c7e307c9534",
#                 "quantity": 1,
#                 "initial_quantity": -1292,
#                 "quantity_in_package": null,
#                 "bar_code": null,
#                 "product_type": "NORMAL",
#                 "mark": null,
#                 "mark_data": null,
#                 "alcohol_by_volume": 0,
#                 "alcohol_product_kind_code": 0,
#                 "tare_volume": 0,
#                 "code": "16",
#                 "product_name": "Чай чашка",
#                 "measure_name": "шт",
#                 "id": 406558,
#                 "uuid": "ab334682-1445-46d9-8ee1-c63c34dd050b",
#                 "extra_keys": [],
#                 "sub_positions": [],
#                 "measure_precision": 0,
#                 "price": 90,
#                 "cost_price": 0,
#                 "result_price": 90,
#                 "sum": 90,
#                 "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
#                 "result_sum": 90,
#                 "position_discount": null,
#                 "doc_distributed_discount": null,
#                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                 "splitted_positions": null,
#                 "attributes_choices": null,
#                 "settlement_method": {"type": "CHECKOUT_FULL", "amount": null},
#                 "agent_requisites": null,
#             },
#             {
#                 "product_id": "797f6172-96f6-4eb3-ad3f-9f3e7042e580",
#                 "quantity": 1,
#                 "initial_quantity": -4934,
#                 "quantity_in_package": null,
#                 "bar_code": null,
#                 "product_type": "NORMAL",
#                 "mark": null,
#                 "mark_data": null,
#                 "alcohol_by_volume": 0,
#                 "alcohol_product_kind_code": 0,
#                 "tare_volume": 0,
#                 "code": "9",
#                 "product_name": "Торт",
#                 "measure_name": "шт",
#                 "id": 406560,
#                 "uuid": "20c2c468-35c6-4419-82b5-6330b7c2c5be",
#                 "extra_keys": [],
#                 "sub_positions": [],
#                 "measure_precision": 0,
#                 "price": 350,
#                 "cost_price": 0,
#                 "result_price": 350,
#                 "sum": 350,
#                 "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
#                 "result_sum": 350,
#                 "position_discount": null,
#                 "doc_distributed_discount": null,
#                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                 "splitted_positions": null,
#                 "attributes_choices": null,
#                 "settlement_method": {"type": "CHECKOUT_FULL", "amount": null},
#                 "agent_requisites": null,
#             },
#         ],
#         "doc_discounts": [],
#         "payments": [
#             {
#                 "id": "c362b31f-edea-4e43-b26e-c250b20220af",
#                 "parent_id": null,
#                 "sum": 440,
#                 "type": "ELECTRON",
#                 "parts": [
#                     {
#                         "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                         "part_sum": 440,
#                         "change": 0,
#                     }
#                 ],
#                 "app_payment": null,
#                 "merchant_info": {
#                     "number": "123",
#                     "english_name": "123",
#                     "category_code": "123",
#                 },
#                 "bank_info": {"name": "ПАО СБЕРБАНК"},
#                 "app_info": {"app_id": null, "name": "Банковская карта"},
#                 "cashless_info": null,
#                 "driver_info": null,
#             }
#         ],
#         "print_groups": [
#             {
#                 "id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                 "type": "CASH_RECEIPT",
#                 "org_name": null,
#                 "org_inn": null,
#                 "org_address": null,
#                 "taxation_system": null,
#                 "medicine_attributes": null,
#             }
#         ],
#         "pos_print_results": [
#             {
#                 "receipt_number": 9217,
#                 "document_number": 20338,
#                 "session_number": 228,
#                 "receipt_date": "23022025",
#                 "receipt_time": "1236",
#                 "fn_reg_number": null,
#                 "fiscal_sign_doc_number": "3667881813",
#                 "fiscal_document_number": 49340,
#                 "fn_serial_number": "7382440700036332",
#                 "kkt_serial_number": "00307900652283",
#                 "kkt_reg_number": "0008200608019020",
#                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                 "check_sum": 440,
#             }
#         ],
#         "sum": 440,
#         "result_sum": 440,
#         "customer_email": null,
#         "customer_phone": null,
#     },
#     "counterparties": null,
#     "created_at": "2025-02-23T05:36:47.175+0000",
#     "version": "V2",
# }


# {
#     "type": "PAYBACK",
#     "id": "0fade32b-67e1-4d41-9742-2747f97d37f3",
#     "extras": {},
#     "number": 50258,
#     "close_date": "2025-02-23T05:46:57.000+0000",
#     "time_zone_offset": 25200000,
#     "session_id": "e16daae2-567f-4718-84cf-dbf9f973ab1c",
#     "session_number": 229,
#     "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
#     "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
#     "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
#     "user_id": "01-000000010409029",
#     "body": {
#         "positions": [
#             {
#                 "product_id": "7ae0a004-45b3-40fb-985f-6c7e307c9534",
#                 "quantity": 1,
#                 "initial_quantity": -1293,
#                 "quantity_in_package": null,
#                 "bar_code": null,
#                 "product_type": "NORMAL",
#                 "mark": null,
#                 "mark_data": null,
#                 "alcohol_by_volume": 0,
#                 "alcohol_product_kind_code": 0,
#                 "tare_volume": 0,
#                 "code": "16",
#                 "product_name": "Чай чашка",
#                 "measure_name": "шт",
#                 "id": 406643,
#                 "uuid": "ab334682-1445-46d9-8ee1-c63c34dd050b",
#                 "extra_keys": [],
#                 "sub_positions": [],
#                 "measure_precision": 0,
#                 "price": 90,
#                 "cost_price": 0,
#                 "result_price": 90,
#                 "sum": 90,
#                 "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
#                 "result_sum": 90,
#                 "position_discount": null,
#                 "doc_distributed_discount": null,
#                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                 "splitted_positions": null,
#                 "attributes_choices": null,
#                 "settlement_method": {"type": "CHECKOUT_FULL", "amount": null},
#                 "agent_requisites": null,
#             }
#         ],
#         "doc_discounts": [],
#         "payments": [
#             {
#                 "id": "3ff4d3a7-de7f-4986-ae76-d9889a5b4e24",
#                 "parent_id": null,
#                 "sum": 90,
#                 "type": "ELECTRON",
#                 "parts": [
#                     {
#                         "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                         "part_sum": 90,
#                         "change": 0,
#                     }
#                 ],
#                 "app_payment": null,
#                 "merchant_info": {
#                     "number": "123",
#                     "english_name": "123",
#                     "category_code": "123",
#                 },
#                 "bank_info": {"name": "ПАО СБЕРБАНК"},
#                 "app_info": {"app_id": null, "name": "Банковская карта"},
#                 "cashless_info": null,
#                 "driver_info": null,
#             }
#         ],
#         "print_groups": [
#             {
#                 "id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                 "type": "CASH_RECEIPT",
#                 "org_name": null,
#                 "org_inn": null,
#                 "org_address": null,
#                 "taxation_system": null,
#                 "medicine_attributes": null,
#             }
#         ],
#         "pos_print_results": [
#             {
#                 "receipt_number": 9228,
#                 "document_number": 20349,
#                 "session_number": 228,
#                 "receipt_date": "23022025",
#                 "receipt_time": "1247",
#                 "fn_reg_number": null,
#                 "fiscal_sign_doc_number": "3358391084",
#                 "fiscal_document_number": 49351,
#                 "fn_serial_number": "7382440700036332",
#                 "kkt_serial_number": "00307900652283",
#                 "kkt_reg_number": "0008200608019020",
#                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                 "check_sum": 90,
#             }
#         ],
#         "sum": 90,
#         "result_sum": 90,
#         "customer_email": null,
#         "customer_phone": null,
#         "base_document_id": "81f72cae-11b6-465b-be75-03b64bd1d58b",
#         "base_document_number": 50247,
#     },
#     "counterparties": null,
#     "created_at": "2025-02-23T05:46:58.326+0000",
#     "version": "V2",
# }
