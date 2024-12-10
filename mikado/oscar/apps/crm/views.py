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

    # def get(self, request, *args, **kwargs):
    #     return self.post(request, *args, **kwargs)

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
        # request_type = "SELL"

        if request_type == "SELL":
            # self.sell(data, *args, **kwargs)
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
            body=f"Добавлен оффлайн заказ: { data.get('id', 'ID Неизвестен') }",
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



        # data = {
        #     "type": "SELL",
        #     "id": "5730a698-cf0d-463d-998a-7f4934638126",
        #     "extras": {},
        #     "number": 31601,
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
        #                 "sum": 70,
        #                 "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
        #                 "result_sum": 140,
        #                 "position_discount": {
        #                     "discount_sum": 140,
        #                     "discount_percent": 50,
        #                     "discount_type": "SUM",
        #                     "coupon": None,
        #                     "discount_price": 70,
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
        #     "id": "24fbebfb-af35-46b8-ab57-4e801b466399",
        #     "extras": {},
        #     "number": 31990,
        #     "close_date": "2024-12-06T05:57:07.000+0000",
        #     "time_zone_offset": 25200000,
        #     "session_id": "0ee885c2-04f7-4828-9364-fd1061a68b90",
        #     "session_number": 150,
        #     "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
        #     "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
        #     "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
        #     "user_id": "01-000000010409029",
        #     "body": {
        #         "positions": [
        #             {
        #                 "product_id": "ac0a279a-6eda-49c6-afba-f2c093c2ac49",
        #                 "quantity": 1,
        #                 "initial_quantity": -168,
        #                 "quantity_in_package": None,
        #                 "bar_code": None,
        #                 "product_type": "NORMAL",
        #                 "mark": None,
        #                 "mark_data": None,
        #                 "alcohol_by_volume": 0,
        #                 "alcohol_product_kind_code": 0,
        #                 "tare_volume": 0,
        #                 "code": "95",
        #                 "product_name": "сэндвич",
        #                 "measure_name": "шт",
        #                 "id": 239576,
        #                 "uuid": "a3889792-75b7-4e10-b5bd-a21c7b6e25a0",
        #                 "extra_keys": [],
        #                 "sub_positions": [],
        #                 "measure_precision": 0,
        #                 "price": 320,
        #                 "cost_price": 0,
        #                 "result_price": 160,
        #                 "sum": 320,
        #                 "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
        #                 "result_sum": 160,
        #                 "position_discount": None,
        #                 "doc_distributed_discount": {
        #                     "discount_sum": 160,
        #                     "discount_percent": 50,
        #                     "discount_type": "SUM",
        #                     "coupon": None,
        #                     "discount_price": None,
        #                 },
        #                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                 "splitted_positions": None,
        #                 "attributes_choices": None,
        #                 "settlement_method": {
        #                     "type": "CHECKOUT_FULL",
        #                     "amount": None,
        #                 },
        #                 "agent_requisites": None,
        #             }
        #         ],
        #         "doc_discounts": [
        #             {
        #                 "discount_sum": 160,
        #                 "discount_percent": 50,
        #                 "discount_type": "SUM",
        #                 "coupon": None,
        #             }
        #         ],
        #         "payments": [
        #             {
        #                 "id": "368f8874-ec08-44a3-98b1-e3e56f665535",
        #                 "parent_id": None,
        #                 "sum": 160,
        #                 "type": "ELECTRON",
        #                 "parts": [
        #                     {
        #                         "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                         "part_sum": 160,
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
        #                 "receipt_number": 284,
        #                 "document_number": 299,
        #                 "session_number": 149,
        #                 "receipt_date": "06122024",
        #                 "receipt_time": "1257",
        #                 "fn_reg_number": None,
        #                 "fiscal_sign_doc_number": "3455354808",
        #                 "fiscal_document_number": 30418,
        #                 "fn_serial_number": "7382440700036332",
        #                 "kkt_serial_number": "00307900652283",
        #                 "kkt_reg_number": "0008200608019020",
        #                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
        #                 "check_sum": 160,
        #             }
        #         ],
        #         "sum": 320,
        #         "result_sum": 160,
        #         "customer_email": None,
        #         "customer_phone": None,
        #     },
        #     "counterparties": None,
        #     "created_at": "2024-12-06T05:57:45.228+0000",
        #     "version": "V2",
        # }
