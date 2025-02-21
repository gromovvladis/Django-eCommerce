from datetime import timedelta
import requests
import logging

from django.conf import settings
from django.contrib.auth.models import Group
from django.utils.timezone import now
from django.db.models.functions import Coalesce, Greatest
from django.db.models import F

from oscar.apps.customer.serializers import UserGroupSerializer, StaffSerializer
from oscar.apps.order.serializers import OrderSerializer
from oscar.core.loading import get_model
from oscar.apps.catalogue.serializers import (
    AdditionalSerializer,
    AdditionalsSerializer,
    ProductGroupSerializer,
    ProductGroupsSerializer,
    ProductSerializer,
    ProductsSerializer,
)
from oscar.apps.store.serializers import (
    StoreSerializer,
    TerminalSerializer,
    StoreCashTransactionSerializer,
    StockRecordOperationSerializer,
)

Store = get_model("store", "Store")
Terminal = get_model("store", "Terminal")
Product = get_model("catalogue", "Product")
Order = get_model("order", "Order")
Additional = get_model("catalogue", "Additional")

CRMMobileCashierToken = None

logger = logging.getLogger("oscar.crm")

evator_cloud_token = settings.EVOTOR_CLOUD_TOKEN

cashier_login = None
cashier_pass = None


# ================= запросы к терминалам (Отправка заказов) =================


class EvotorAPIMobileCashier:
    """ "
    Документация для внедрения по ссылке ниже

    ТОКЕН МОБИЛЬНОГО КАССИРА (Для отправки запросов к текрминалам)

    """

    def __init__(
        self, base_url: str = "https://fiscalization-test.evotor.ru/possystem/v5/"
    ):
        """
        Инициализация клиента для работы с API Эвотор Облако.

        :param api_token: Токен приложения для авторизации в API.
        :param base_url: Базовый URL для API. По умолчанию 'https://fiscalization.evotor.ru/possystem/v5/'. Для запросов к кассе
        """
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json; charset=utf-8",
        }
        self.headers["Token"] = self.get_mobilecashier_token()

    def send_request(
        self, endpoint: str, method: str = "GET", data: dict = None, bulk: bool = False
    ):
        """
        Отправка HTTP-запроса к Эвотор API.

        :param endpoint: Конечная точка API (без базового URL).
        :param method: HTTP-метод (GET, POST, PUT, DELETE).
        :param data: Данные для отправки в теле запроса (для методов POST/PUT).
        :return: Ответ от API в формате JSON.
        """
        url = self.base_url + endpoint

        if bulk:
            self.headers["Content-Type"] = "application/vnd.evotor.v2+bulk+json"
        else:
            self.headers["Content-Type"] = "application/vnd.evotor.v2+json"

        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                logger.error(f"Ошибка HTTP запроса. Неизвестный http метод: {method}")
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()  # Проверка на успешный статус запроса (2xx)
            return response.json()  # Возврат данных в формате JSON

        except requests.exceptions.HTTPError as http_err:
            error = ""
            if response.status_code == 400:
                error = "Неверный запрос Эвотор."
            if response.status_code == 401:
                error = "Ошибка авторизации приложения Эвотор."
            elif response.status_code == 402:
                error = (
                    "Приложение Эвотор не установлено на одно или несколько устройств."
                )
            elif response.status_code == 403:
                error = "Нет доступа Эвотор. Ошибка возникает когда у приложения нет разрешения на запрашиваемое действие или пользователь не установил приложение в Личном кабинете."
            elif response.status_code == 404:
                error = "Запрашиваемый ресурс не найден в Эвотор."
            elif response.status_code == 405:
                error = "Недопустимый метод запроса в Эвотор."
            elif response.status_code == 406:
                error = "Тип содержимого, которое возвращает ресурс не соответствует типу содержимого, которое указанно в заголовке Accept Эвотор."
            elif response.status_code == 429:
                error = "Превышено максимальное количество запросов Эвотор в текущем периоде."
            logger.error(f"Ошибка HTTP запроса при отправке Эвотор запроса: {http_err}")
            return {"error": error}
        except Exception as err:
            if response.status_code == 204:
                return {}
            logger.error(f"Ошибка при отправке Эвотор запроса: {err}")
            return {"error": f"Ошибка при отправке Эвотор запроса: {err}"}

    def get_mobilecashier_token(self):

        cashier_token = CRMMobileCashierToken.objects.first()
        current_time = now()

        if cashier_token and (current_time - cashier_token.created_at) < timedelta(
            hours=23
        ):
            return cashier_token.token
        else:
            if cashier_token:
                cashier_token.delete()

            auth_data = {"login": cashier_login, "pass": cashier_pass}

            endpoint = f"getToken"
            response = self.send_request(endpoint, "POST", auth_data)

            token = response.get("token", None)

            if token is not None:
                CRMMobileCashierToken.objects.create(token=token)

            return token


class EvotorMobileCashier(EvotorAPIMobileCashier):

    def send_order(self, order_json):
        """
        Регистрация чека с операцией «Приход»
        https://docs.evotor.online/api/opisanie-api-konnektor-atol-onlain

        """
        endpoint = f"{cashier_group_code}/sell"
        response = self.send_request(endpoint, "POST", order_json)
        error = response.get("error", None) if isinstance(response, dict) else None

        if not error:
            order_id = order_json.get("external_id", None)
            if order_id:
                order = Order.objects.get(id=order_id)
                order.evotor_id = response.get("uuid")
                order.save()

    def cancel_order(self, order_json):
        """
        https://mobilecashier.ru/api/v4/asc/create/{userId}
        """
        endpoint = f"<group_code>/sell_refund"
        response = self.send_request(endpoint, "POST", order_json)
        error = response.get("error", None) if isinstance(response, dict) else None

        # if not error:
        # order.refund
