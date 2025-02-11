import json
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from django.conf import settings
from django.http import JsonResponse

from oscar.apps.crm.client import EvatorCloud
from oscar.apps.telegram.models import TelegramMessage
from oscar.core.loading import get_model
from oscar.apps.telegram.bot.synchron.send_message import send_message_to_staffs

CRMEvent = get_model("crm", "CRMEvent")
Store = get_model("store", "Store")

logger = logging.getLogger("oscar.crm")

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


class CRMInstallationEndpointView(APIView):
    """https://mikado-sushi.ru/crm/api/subscription/setup"""

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

        CRMEvent.objects.create(
            body=f"Terminals recived {request.data}",
            sender=CRMEvent.INSTALLATION,
            event_type=CRMEvent.INFO,
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

        not_allowed = is_valid_site_and_user_tokens(request)
        if not_allowed:
            return not_allowed

        return Response(
            {"userId": request.data.get("userId"), "token": user_token},
            status=status.HTTP_200_OK,
        )


class CRMStoreEndpointView(APIView):
    """https://mikado-sushi.ru/crm/api/stores"""

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
            stores.append(store_json.get("id", "Магазин"))

        CRMEvent.objects.create(
            body=f"Добавлены или изменены магазины: {', '.join(stores)}",
            sender=CRMEvent.STORE,
            event_type=CRMEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_stores(stores_json)

        return JsonResponse({"status": "ok"}, status=200)


class CRMTerminalEndpointView(APIView):
    """https://mikado-sushi.ru/crm/api/terminals"""

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

        CRMEvent.objects.create(
            body=f"Добавлены или изменены терминалы: {', '.join(terminals)}",
            sender=CRMEvent.TERMINAL,
            event_type=CRMEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_terminals(terminals_json)

        return JsonResponse({"status": "ok"}, status=200)


class CRMStaffEndpointView(APIView):
    """https://mikado-sushi.ru/crm/api/staffs"""

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
            staffs.append(staff_json.get("id", "Сотрудник"))

        CRMEvent.objects.create(
            body=f"Добавлены или изменены сотрудники: {', '.join(staffs)}",
            sender=CRMEvent.STAFF,
            event_type=CRMEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_staffs(staffs_json)

        return JsonResponse({"status": "ok"}, status=200)


class CRMRoleEndpointView(APIView):
    """https://mikado-sushi.ru/crm/api/roles"""

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
            roles.append(role_json.get("id", "Роль сотрудников"))

        CRMEvent.objects.create(
            body=f"Добавлены или изменены роли сотрудников: {', '.join(roles)}",
            sender=CRMEvent.STAFF,
            event_type=CRMEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_roles(roles_json)

        return JsonResponse({"status": "ok"}, status=200)


class CRMProductEndpointView(APIView):
    """https://mikado-sushi.ru/crm/api/stores/<str:store_id>/products/"""

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

        CRMEvent.objects.create(
            body=f"Добавлены или изменены товары: {', '.join(products)}",
            sender=CRMEvent.PRODUCT,
            event_type=CRMEvent.UPDATE,
        )

        EvatorCloud().create_or_update_site_products(products_json)

        return JsonResponse({"status": "success"}, status=200)


class CRMDocsEndpointView(APIView):
    """
    https://mikado-sushi.ru/crm/api/docs

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
        send_message_to_staffs(
            f"request: {json.dumps(request_info, ensure_ascii=False)}",
            TelegramMessage.TECHNICAL,
        )

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed

        request_type = request.data.get("type")

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
            CRMEvent.objects.create(
                body="Error: Неподдерживаемый тип документа.",
                sender=CRMEvent.DOC,
                event_type=CRMEvent.ERROR,
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



        # data = {
        #     "type": "SELL",
        #     "id": "5530a698-cf0d-463d-g464-7f4934638126",
        #     "extras": {},
        #     "number": 18640,
        #     "close_date": "2024-12-09T04:43:48.000+0000",
        #     "time_zone_offset": 25200000,
        #     "session_id": "047908c2-7546-469b-bc1b-ba5477de60fd",
        #     "session_number": 153,
        #     "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
        #     "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
        #     "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
        #     "user_id": "01-000000010409029",
        #     "body": {
        #         "positions": [
        #             {
        #                 "product_id": "f0d98ed6-84ae-4e04-b575-16bf3a1f376f",
        #                 "quantity": 2,
        #                 "initial_quantity": -175,
        #                 "quantity_in_package": None,
        #                 "bar_code": None,
        #                 "product_type": "NORMAL",
        #                 "mark": None,
        #                 "mark_data": None,
        #                 "alcohol_by_volume": 0,
        #                 "alcohol_product_kind_code": 0,
        #                 "tare_volume": 0,
        #                 "code": "33",
        #                 "product_name": "Молоко альтернативное",
        #                 "measure_name": "шт",
        #                 "id": 245355,
        #                 "uuid": "3c07a1d0-8987-40fd-9419-989c3fab4ff2",
        #                 "extra_keys": [],
        #                 "sub_positions": [],
        #                 "measure_precision": 0,
        #                 "price": 70,
        #                 "cost_price": 0,
        #                 "result_price": 35,
        #                 "sum": 140,
        #                 "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
        #                 "result_sum": 70,
        #                 "position_discount": {
        #                     "discount_sum": 70,
        #                     "discount_percent": 50,
        #                     "discount_type": "SUM",
        #                     "coupon": 1234,
        #                     "discount_price": 35,
        #                 },
        #                 "doc_distributed_discount": None,
        #                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                 "splitted_positions": None,
        #                 "attributes_choices": None,
        #                 "settlement_method": {"type": "CHECKOUT_FULL", "amount": None},
        #                 "agent_requisites": None,
        #             },
        #             {
        #                 "product_id": "d5721912-ab36-49ed-9447-db2fc81529ad",
        #                 "quantity": 2,
        #                 "initial_quantity": -47,
        #                 "quantity_in_package": None,
        #                 "bar_code": None,
        #                 "product_type": "NORMAL",
        #                 "mark": None,
        #                 "mark_data": None,
        #                 "alcohol_by_volume": 0,
        #                 "alcohol_product_kind_code": 0,
        #                 "tare_volume": 0,
        #                 "code": "20",
        #                 "product_name": "Раф классика 0,4",
        #                 "measure_name": "шт",
        #                 "id": 245357,
        #                 "uuid": "f77cfac1-9cad-4e1e-ba70-fcdba07e7f66",
        #                 "extra_keys": [],
        #                 "sub_positions": [],
        #                 "measure_precision": 0,
        #                 "price": 340,
        #                 "cost_price": 0,
        #                 "result_price": 170,
        #                 "sum": 680,
        #                 "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
        #                 "result_sum": 340,
        #                 "position_discount": {
        #                     "discount_sum": 340,
        #                     "discount_percent": 50,
        #                     "discount_type": "SUM",
        #                     "coupon": None,
        #                     "discount_price": 170,
        #                 },
        #                 "doc_distributed_discount": None,
        #                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                 "splitted_positions": None,
        #                 "attributes_choices": None,
        #                 "settlement_method": {"type": "CHECKOUT_FULL", "amount": None},
        #                 "agent_requisites": None,
        #             },
        #         ],
        #         "doc_discounts": [],
        #         "payments": [
        #             {
        #                 "id": "02f1d188-9321-47de-9369-d60b097e4502",
        #                 "parent_id": None,
        #                 "sum": 480,
        #                 "type": "ELECTRON",
        #                 "parts": [
        #                     {
        #                         "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                         "part_sum": 480,
        #                         "change": 0,
        #                     }
        #                 ],
        #                 "app_payment": None,
        #                 "merchant_info": {
        #                     "number": "123",
        #                     "english_name": "123",
        #                     "category_code": "123",
        #                 },
        #                 "bank_info": {"name": "ПАО СБЕРБАНК"},
        #                 "app_info": {"app_id": None, "name": "Банковская карта"},
        #             }
        #         ],
        #         "print_groups": [
        #             {
        #                 "id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                 "type": "CASH_RECEIPT",
        #                 "org_name": None,
        #                 "org_inn": None,
        #                 "org_address": None,
        #                 "taxation_system": None,
        #                 "medicine_attributes": None,
        #             }
        #         ],
        #         "pos_print_results": [
        #             {
        #                 "receipt_number": 945,
        #                 "document_number": 992,
        #                 "session_number": 152,
        #                 "receipt_date": "09122024",
        #                 "receipt_time": "1143",
        #                 "fn_reg_number": None,
        #                 "fiscal_sign_doc_number": "3262381307",
        #                 "fiscal_document_number": 31079,
        #                 "fn_serial_number": "7382440700036332",
        #                 "kkt_serial_number": "00307900652283",
        #                 "kkt_reg_number": "0008200608019020",
        #                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                 "check_sum": 480,
        #             }
        #         ],
        #         "sum": 820,
        #         "result_sum": 480,
        #         "customer_email": None,
        #         "customer_phone": None,
        #     },
        #     "counterparties": None,
        #     "created_at": "2024-12-09T03:25:02.976+0000",
        #     "version": "V2",
        # }

        # data = {
        #     "type": "SELL",
        #     "id": "5730a698-cf0d-463d-998a-7f49a4038124",
        #     "extras": {},
        #     "number": 31671,
        #     "close_date": "2024-12-09T04:43:48.000+0000",
        #     "time_zone_offset": 25200000,
        #     "session_id": "047908c2-7546-469b-bc1b-ba5477de60fd",
        #     "session_number": 153,
        #     "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
        #     "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
        #     "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
        #     "user_id": "01-000000010409029",
        #     "body": {
        #         "positions": [
        #             {
        #                 "product_id": "f0d98ed6-84ae-4e04-b575-16bf3a1f376f",
        #                 "quantity": 2,
        #                 "initial_quantity": -175,
        #                 "quantity_in_package": None,
        #                 "bar_code": None,
        #                 "product_type": "NORMAL",
        #                 "mark": None,
        #                 "mark_data": None,
        #                 "alcohol_by_volume": 0,
        #                 "alcohol_product_kind_code": 0,
        #                 "tare_volume": 0,
        #                 "code": "33",
        #                 "product_name": "Молоко альтернативное",
        #                 "measure_name": "шт",
        #                 "id": 245355,
        #                 "uuid": "3c07a1d0-8987-40fd-9419-989c3fab4ff2",
        #                 "extra_keys": [],
        #                 "sub_positions": [],
        #                 "measure_precision": 0,
        #                 "price": 70,
        #                 "cost_price": 0,
        #                 "result_price": 70,
        #                 "sum": 140,
        #                 "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
        #                 "result_sum": 140,
        #                 "position_discount": None,
        #                 "doc_distributed_discount": None,
        #                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                 "splitted_positions": None,
        #                 "attributes_choices": None,
        #                 "settlement_method": {"type": "CHECKOUT_FULL", "amount": None},
        #                 "agent_requisites": None,
        #             },
        #             {
        #                 "product_id": "d5721912-ab36-49ed-9447-db2fc81529ad",
        #                 "quantity": 2,
        #                 "initial_quantity": -47,
        #                 "quantity_in_package": None,
        #                 "bar_code": None,
        #                 "product_type": "NORMAL",
        #                 "mark": None,
        #                 "mark_data": None,
        #                 "alcohol_by_volume": 0,
        #                 "alcohol_product_kind_code": 0,
        #                 "tare_volume": 0,
        #                 "code": "20",
        #                 "product_name": "Раф классика 0,4",
        #                 "measure_name": "шт",
        #                 "id": 245357,
        #                 "uuid": "f77cfac1-9cad-4e1e-ba70-fcdba07e7f66",
        #                 "extra_keys": [],
        #                 "sub_positions": [],
        #                 "measure_precision": 0,
        #                 "price": 340,
        #                 "cost_price": 0,
        #                 "result_price": 170,
        #                 "sum": 680,
        #                 "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
        #                 "result_sum": 340,
        #                 "position_discount": {
        #                     "discount_sum": 340,
        #                     "discount_percent": 50,
        #                     "discount_type": "SUM",
        #                     "coupon": None,
        #                     "discount_price": 170,
        #                 },
        #                 "doc_distributed_discount": None,
        #                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                 "splitted_positions": None,
        #                 "attributes_choices": None,
        #                 "settlement_method": {"type": "CHECKOUT_FULL", "amount": None},
        #                 "agent_requisites": None,
        #             },
        #         ],
        #         "doc_discounts": [],
        #         "payments": [
        #             {
        #                 "id": "02f1d188-9321-47de-9369-d60b097e4502",
        #                 "parent_id": None,
        #                 "sum": 480,
        #                 "type": "ELECTRON",
        #                 "parts": [
        #                     {
        #                         "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                         "part_sum": 480,
        #                         "change": 0,
        #                     }
        #                 ],
        #                 "app_payment": None,
        #                 "merchant_info": {
        #                     "number": "123",
        #                     "english_name": "123",
        #                     "category_code": "123",
        #                 },
        #                 "bank_info": {"name": "ПАО СБЕРБАНК"},
        #                 "app_info": {"app_id": None, "name": "Банковская карта"},
        #             }
        #         ],
        #         "print_groups": [
        #             {
        #                 "id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                 "type": "CASH_RECEIPT",
        #                 "org_name": None,
        #                 "org_inn": None,
        #                 "org_address": None,
        #                 "taxation_system": None,
        #                 "medicine_attributes": None,
        #             }
        #         ],
        #         "pos_print_results": [
        #             {
        #                 "receipt_number": 945,
        #                 "document_number": 992,
        #                 "session_number": 152,
        #                 "receipt_date": "09122024",
        #                 "receipt_time": "1143",
        #                 "fn_reg_number": None,
        #                 "fiscal_sign_doc_number": "3262381307",
        #                 "fiscal_document_number": 31079,
        #                 "fn_serial_number": "7382440700036332",
        #                 "kkt_serial_number": "00307900652283",
        #                 "kkt_reg_number": "0008200608019020",
        #                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                 "check_sum": 480,
        #             }
        #         ],
        #         "sum": 820,
        #         "result_sum": 480,
        #         "customer_email": None,
        #         "customer_phone": None,
        #     },
        #     "counterparties": None,
        #     "created_at": "2024-12-09T04:43:51.023+0000",
        #     "version": "V2",
        # }

        # data = {
        #         "type": "SELL",
        #         "id": "24fbebfb-af35-46b8-ab57-4e801b466399",
        #         "extras": {},
        #         "number": 31990,
        #         "close_date": "2024-12-06T05:57:07.000+0000",
        #         "time_zone_offset": 25200000,
        #         "session_id": "0ee885c2-04f7-4828-9364-fd1061a68b90",
        #         "session_number": 150,
        #         "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
        #         "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
        #         "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
        #         "user_id": "01-000000010409029",
        #         "body": {
        #             "positions": [
        #                 {
        #                     "product_id": "ac0a279a-6eda-49c6-afba-f2c093c2ac49",
        #                     "quantity": 1,
        #                     "initial_quantity": -168,
        #                     "quantity_in_package": None,
        #                     "bar_code": None,
        #                     "product_type": "NORMAL",
        #                     "mark": None,
        #                     "mark_data": None,
        #                     "alcohol_by_volume": 0,
        #                     "alcohol_product_kind_code": 0,
        #                     "tare_volume": 0,
        #                     "code": "95",
        #                     "product_name": "сэндвич",
        #                     "measure_name": "шт",
        #                     "id": 239576,
        #                     "uuid": "a3889792-75b7-4e10-b5bd-a21c7b6e25a0",
        #                     "extra_keys": [],
        #                     "sub_positions": [],
        #                     "measure_precision": 0,
        #                     "price": 320,
        #                     "cost_price": 0,
        #                     "result_price": 160,
        #                     "sum": 320,
        #                     "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
        #                     "result_sum": 160,
        #                     "position_discount": None,
        #                     "doc_distributed_discount": {
        #                         "discount_sum": 160,
        #                         "discount_percent": 50,
        #                         "discount_type": "SUM",
        #                         "coupon": None,
        #                         "discount_price": None,
        #                     },
        #                     "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                     "splitted_positions": None,
        #                     "attributes_choices": None,
        #                     "settlement_method": {
        #                         "type": "CHECKOUT_FULL",
        #                         "amount": None,
        #                     },
        #                     "agent_requisites": None,
        #                 }
        #             ],
        #             "doc_discounts": [
        #                 {
        #                     "discount_sum": 160,
        #                     "discount_percent": 50,
        #                     "discount_type": "SUM",
        #                     "coupon": None,
        #                 }
        #             ],
        #             "payments": [
        #                 {
        #                     "id": "368f8874-ec08-44a3-98b1-e3e56f665535",
        #                     "parent_id": None,
        #                     "sum": 160,
        #                     "type": "ELECTRON",
        #                     "parts": [
        #                         {
        #                             "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                             "part_sum": 160,
        #                             "change": 0,
        #                         }
        #                     ],
        #                     "app_payment": None,
        #                     "merchant_info": {
        #                         "number": "123",
        #                         "english_name": "123",
        #                         "category_code": "123",
        #                     },
        #                     "bank_info": {"name": "ПАО СБЕРБАНК"},
        #                     "app_info": {"app_id": None, "name": "Банковская карта"},
        #                 }
        #             ],
        #             "print_groups": [
        #                 {
        #                     "id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                     "type": "CASH_RECEIPT",
        #                     "org_name": None,
        #                     "org_inn": None,
        #                     "org_address": None,
        #                     "taxation_system": None,
        #                     "medicine_attributes": None,
        #                 }
        #             ],
        #             "pos_print_results": [
        #                 {
        #                     "receipt_number": 284,
        #                     "document_number": 299,
        #                     "session_number": 149,
        #                     "receipt_date": "06122024",
        #                     "receipt_time": "1257",
        #                     "fn_reg_number": None,
        #                     "fiscal_sign_doc_number": "3455354808",
        #                     "fiscal_document_number": 30418,
        #                     "fn_serial_number": "7382440700036332",
        #                     "kkt_serial_number": "00307900652283",
        #                     "kkt_reg_number": "0008200608019020",
        #                     "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                     "check_sum": 160,
        #                 }
        #             ],
        #             "sum": 320,
        #             "result_sum": 160,
        #             "customer_email": None,
        #             "customer_phone": None,
        #         },
        #         "counterparties": None,
        #         "created_at": "2024-12-06T05:57:45.228+0000",
        #         "version": "V2",
        #     }


# {
#     "method": "PUT",
#     "path": "/crm/api/docs/",
#     "headers": {
#         "Host": "provence-coffee.ru",
#         "X-Real-Ip": "185.170.204.77",
#         "X-Forwarded-For": "185.170.204.77",
#         "Connection": "close",
#         "Content-Length": "2450",
#         "Accept": "application/json, application/*+json",
#         "Content-Type": "application/json",
#         "Authorization": "Bearer 9179d780-56a4-49ea-b042-435e3257eaf8",
#         "X-Evotor-User-Id": "01-000000010409029",
#         "X-B3-Traceid": "68aa3bda4cc5572b",
#         "X-B3-Spanid": "0f5eb3fc52acab73",
#         "X-B3-Parentspanid": "68aa3bda4cc5572b",
#         "X-B3-Sampled": "0",
#         "User-Agent": "Java/1.8.0_151",
#     },
#     "data": {
#         "type": "PAYBACK",
#         "id": "d7a11cd2-fb23-4999-9dc2-5a97c8227dd5",
#         "extras": {},
#         "number": 45376,
#         "close_date": "2025-02-02T10:18:08.000+0000",
#         "time_zone_offset": 25200000,
#         "session_id": "6580cf44-739d-476e-aa37-49385bfdabcc",
#         "session_number": 208,
#         "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
#         "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
#         "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
#         "user_id": "01-000000010409029",
#         "body": {
#             "positions": [
#                 {
#                     "product_id": "14ffc31e-8ea3-4e58-98c3-d3ef8a98a26c",
#                     "quantity": 1,
#                     "initial_quantity": -1941,
#                     "quantity_in_package": null,
#                     "bar_code": null,
#                     "product_type": "NORMAL",
#                     "mark": null,
#                     "mark_data": null,
#                     "alcohol_by_volume": 0,
#                     "alcohol_product_kind_code": 0,
#                     "tare_volume": 0,
#                     "code": "3",
#                     "product_name": "Американо",
#                     "measure_name": "шт",
#                     "id": 364308,
#                     "uuid": "f874447a-c57b-4a46-b363-571941817b38",
#                     "extra_keys": [],
#                     "sub_positions": [],
#                     "measure_precision": 0,
#                     "price": 190,
#                     "cost_price": 0,
#                     "result_price": 190,
#                     "sum": 190,
#                     "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
#                     "result_sum": 190,
#                     "position_discount": null,
#                     "doc_distributed_discount": null,
#                     "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                     "splitted_positions": null,
#                     "attributes_choices": null,
#                     "settlement_method": {"type": "CHECKOUT_FULL", "amount": null},
#                     "agent_requisites": null,
#                 }
#             ],
#             "doc_discounts": [],
#             "payments": [
#                 {
#                     "id": "f55a31f4-3564-465c-b98d-d75a35fedcfc",
#                     "parent_id": null,
#                     "sum": 190,
#                     "type": "CASH",
#                     "parts": [
#                         {
#                             "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                             "part_sum": 190,
#                             "change": 0,
#                         }
#                     ],
#                     "app_payment": null,
#                     "merchant_info": null,
#                     "bank_info": null,
#                     "app_info": {"app_id": null, "name": "Наличные"},
#                     "cashless_info": null,
#                     "driver_info": null,
#                 }
#             ],
#             "print_groups": [
#                 {
#                     "id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                     "type": "CASH_RECEIPT",
#                     "org_name": null,
#                     "org_inn": null,
#                     "org_address": null,
#                     "taxation_system": null,
#                     "medicine_attributes": null,
#                 }
#             ],
#             "pos_print_results": [
#                 {
#                     "receipt_number": 4430,
#                     "document_number": 15271,
#                     "session_number": 207,
#                     "receipt_date": "02022025",
#                     "receipt_time": "1718",
#                     "fn_reg_number": null,
#                     "fiscal_sign_doc_number": "388533948",
#                     "fiscal_document_number": 44561,
#                     "fn_serial_number": "7382440700036332",
#                     "kkt_serial_number": "00307900652283",
#                     "kkt_reg_number": "0008200608019020",
#                     "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                     "check_sum": 190,
#                 }
#             ],
#             "sum": 190,
#             "result_sum": 190,
#             "customer_email": null,
#             "customer_phone": null,
#             "base_document_id": "01185b34-2b96-4b07-8a3a-a984a6512ecb",
#             "base_document_number": 45375,
#         },
#         "counterparties": null,
#         "created_at": "2025-02-02T10:18:10.007+0000",
#         "version": "V2",
#     },
# }


# {
#     "method": "PUT",
#     "path": "/crm/api/docs/",
#     "headers": {
#         "Host": "provence-coffee.ru",
#         "X-Real-Ip": "185.170.204.77",
#         "X-Forwarded-For": "185.170.204.77",
#         "Connection": "close",
#         "Content-Length": "3956",
#         "Accept": "application/json, application/*+json",
#         "Content-Type": "application/json",
#         "Authorization": "Bearer 9179d780-56a4-49ea-b042-435e3257eaf8",
#         "X-Evotor-User-Id": "01-000000010409029",
#         "X-B3-Traceid": "a2697f32413d00c9",
#         "X-B3-Spanid": "ebbea88f87e95be8",
#         "X-B3-Parentspanid": "a2697f32413d00c9",
#         "X-B3-Sampled": "0",
#         "User-Agent": "Java/1.8.0_151",
#     },
#     "data": {
#         "type": "SELL",
#         "id": "ecf96edf-efa0-491a-8308-0f2d2bf8d453",
#         "extras": {},
#         "number": 40379,
#         "close_date": "2025-01-12T13:28:45.000+0000",
#         "time_zone_offset": 25200000,
#         "session_id": "9f06abb3-b0fc-4d32-9519-5930846ea46b",
#         "session_number": 187,
#         "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
#         "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
#         "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
#         "user_id": "01-000000010409029",
#         "body": {
#             "positions": [
#                 {
#                     "product_id": "2a0f4d45-6dbd-4d96-95dd-d80c4a824656",
#                     "quantity": 1,
#                     "initial_quantity": -2476,
#                     "quantity_in_package": null,
#                     "bar_code": null,
#                     "product_type": "NORMAL",
#                     "mark": null,
#                     "mark_data": null,
#                     "alcohol_by_volume": 0,
#                     "alcohol_product_kind_code": 0,
#                     "tare_volume": 0,
#                     "code": "8",
#                     "product_name": "Кофе 0,4",
#                     "measure_name": "шт",
#                     "id": 320768,
#                     "uuid": "5890d2df-4294-48b5-b61c-73bbeb39c624",
#                     "extra_keys": [],
#                     "sub_positions": [],
#                     "measure_precision": 0,
#                     "price": 310,
#                     "cost_price": 0,
#                     "result_price": 310,
#                     "sum": 310,
#                     "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
#                     "result_sum": 310,
#                     "position_discount": null,
#                     "doc_distributed_discount": null,
#                     "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                     "splitted_positions": null,
#                     "attributes_choices": null,
#                     "settlement_method": {"type": "CHECKOUT_FULL", "amount": null},
#                     "agent_requisites": null,
#                 },
#                 {
#                     "product_id": "3edc36f3-03f9-4e0a-9717-4be906eceace",
#                     "quantity": 1,
#                     "initial_quantity": -997,
#                     "quantity_in_package": null,
#                     "bar_code": null,
#                     "product_type": "NORMAL",
#                     "mark": null,
#                     "mark_data": null,
#                     "alcohol_by_volume": 0,
#                     "alcohol_product_kind_code": 0,
#                     "tare_volume": 0,
#                     "code": "4",
#                     "product_name": "Сироп",
#                     "measure_name": "шт",
#                     "id": 320770,
#                     "uuid": "ee3c0380-aabb-435a-baab-2f93cbba02a9",
#                     "extra_keys": [],
#                     "sub_positions": [],
#                     "measure_precision": 0,
#                     "price": 30,
#                     "cost_price": 0,
#                     "result_price": 30,
#                     "sum": 30,
#                     "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
#                     "result_sum": 30,
#                     "position_discount": null,
#                     "doc_distributed_discount": null,
#                     "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                     "splitted_positions": null,
#                     "attributes_choices": null,
#                     "settlement_method": {"type": "CHECKOUT_FULL", "amount": null},
#                     "agent_requisites": null,
#                 },
#                 {
#                     "product_id": "13111c38-e846-41f7-a723-7914a818eaac",
#                     "quantity": 1,
#                     "initial_quantity": -3219,
#                     "quantity_in_package": null,
#                     "bar_code": null,
#                     "product_type": "NORMAL",
#                     "mark": null,
#                     "mark_data": null,
#                     "alcohol_by_volume": 0,
#                     "alcohol_product_kind_code": 0,
#                     "tare_volume": 0,
#                     "code": "2",
#                     "product_name": "Кофе 0,3",
#                     "measure_name": "шт",
#                     "id": 320772,
#                     "uuid": "42858995-3959-415f-acdf-1c8eeeb86856",
#                     "extra_keys": [],
#                     "sub_positions": [],
#                     "measure_precision": 0,
#                     "price": 280,
#                     "cost_price": 0,
#                     "result_price": 280,
#                     "sum": 280,
#                     "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
#                     "result_sum": 280,
#                     "position_discount": null,
#                     "doc_distributed_discount": null,
#                     "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                     "splitted_positions": null,
#                     "attributes_choices": null,
#                     "settlement_method": {"type": "CHECKOUT_FULL", "amount": null},
#                     "agent_requisites": null,
#                 },
#             ],
#             "doc_discounts": [],
#             "payments": [
#                 {
#                     "id": "fddafcf5-db67-4085-8277-9ba7311eed03",
#                     "parent_id": null,
#                     "sum": 1000,
#                     "type": "CASH",
#                     "parts": [
#                         {
#                             "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                             "part_sum": 1000,
#                             "change": 380,
#                         }
#                     ],
#                     "app_payment": null,
#                     "merchant_info": null,
#                     "bank_info": null,
#                     "app_info": {"app_id": null, "name": "Наличные"},
#                     "cashless_info": null,
#                     "driver_info": null,
#                 }
#             ],
#             "print_groups": [
#                 {
#                     "id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                     "type": "CASH_RECEIPT",
#                     "org_name": null,
#                     "org_inn": null,
#                     "org_address": null,
#                     "taxation_system": null,
#                     "medicine_attributes": null,
#                 }
#             ],
#             "pos_print_results": [
#                 {
#                     "receipt_number": 9516,
#                     "document_number": 10088,
#                     "session_number": 186,
#                     "receipt_date": "12012025",
#                     "receipt_time": "2028",
#                     "fn_reg_number": null,
#                     "fiscal_sign_doc_number": "3884633961",
#                     "fiscal_document_number": 39647,
#                     "fn_serial_number": "7382440700036332",
#                     "kkt_serial_number": "00307900652283",
#                     "kkt_reg_number": "0008200608019020",
#                     "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                     "check_sum": 620,
#                 }
#             ],
#             "sum": 620,
#             "result_sum": 620,
#             "customer_email": null,
#             "customer_phone": null,
#         },
#         "counterparties": null,
#         "created_at": "2025-01-12T13:28:47.145+0000",
#         "version": "V2",
#     },
# }
