import json
import requests
import logging
from collections import defaultdict
from django.conf import settings
from django.contrib.auth.models import Group
from django.utils.timezone import now

from rest_framework.renderers import JSONRenderer
from oscar.apps.catalogue.serializers import (
    AdditionalSerializer,
    AdditionalsSerializer,
    ProductGroupSerializer,
    ProductGroupsSerializer,
    ProductSerializer,
    ProductsSerializer,
)
from oscar.apps.customer.serializers import UserGroupSerializer, StaffSerializer
from oscar.apps.order.serializers import OrderSerializer
from oscar.apps.order.utils import OrderCreator
from oscar.apps.store.serializers import StoreSerializer, TerminalSerializer
from oscar.core.loading import get_model
from .tasks import process_bulk_task

logger = logging.getLogger("oscar.crm")

CRMEvent = get_model("crm", "CRMEvent")
CRMBulk = get_model("crm", "CRMBulk")
Store = get_model("store", "Store")
Terminal = get_model("store", "Terminal")
Staff = get_model("user", "Staff")
GroupEvotor = get_model("auth", "GroupEvotor")
Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
AdditionalCategory = get_model("catalogue", "AdditionalCategory")
Order = get_model("order", "Order")
Additional = get_model("catalogue", "Additional")

evator_cloud_token = settings.EVOTOR_CLOUD_TOKEN

cashier_login = settings.MOBILE_CASHIER_LOGIN
cashier_pass = settings.MOBILE_CASHIER_PASSWORD

# ================= запросы к облаку =================


class EvotorAPICloud:
    """ "
    Документация для внедрения по ссылке ниже

    ТОКЕНЫ:

        ТОКЕН ОБЛАКА - ТОКЕН ПРИЛОЖЕНИЯ (ОБЛАКО ПРОВЕРЯЕТ МОИ ЗАПРОСЫ)
            Вебхуки-запросы
                Регистрация новой учётной записи;
                Авторизация существующего пользователя;
                Передача токена Облака Эвотор.


        ТОКЕН ПОЛЬЗОВАТЕЛЯ ПРИЛОЖЕНИЯ (Я ПРОВЕРЯЮ ЗАПРОСЫ ОТ ОБЛАКА)
            Вебхуки-уведомления
                Создать товары;
                Передать документы;
                Создать смарт-терминал;
                Создать сотрудника;
                Создать магазин;
                Отправить чек (V2).


    https://developer.evotor.ru/docs/rest_overview.html
    """

    def __init__(
        self,
        cloud_token: str = evator_cloud_token,  # Токен приложения для авторизации в кассе. Получается у разработчика Эвотор Облако.
        base_url: str = "https://api.evotor.ru/",
    ):
        """
        Инициализация клиента для работы с API Эвотор Облако.

        :param api_token: Токен приложения для авторизации в API.
        :param base_url: Базовый URL для API. По умолчанию 'https://api.evotor.ru/'. Для запросов к облаку
        :param cashier_url: Базовый URL для API. По умолчанию 'https://mobilecashier.ru/api/v2/authorize/'. Для запросов к кассе
        """
        self.cloud_token = cloud_token
        self.base_url = base_url

        self.headers = {
            "X-Authorization": self.cloud_token,
            "Authorization": f"Bearer {self.cloud_token}",
            "Content-Type": "application/vnd.evotor.v2+json",
            "Accept": "application/vnd.evotor.v2+json",
        }

    def handle_response_errors(self, response, errors):
        if isinstance(response, dict) and "error" in response:
            errors.append(response["error"])

    def set_evotor_ids(self, details, model, lookup_field):
        """
        Устанавливает evotor_id для объектов модели на основе данных.
        """
        # Сопоставляем данные из `details` с объектами модели
        lookup_values = [detail.get(lookup_field) for detail in details if detail.get(lookup_field)]
        objects = model.objects.filter(**{f"{lookup_field}__in": lookup_values})
        objects_dict = {getattr(obj, lookup_field): obj for obj in objects}

        for detail in details:
            lookup_value = detail.get(lookup_field)
            if lookup_value and lookup_value in objects_dict:
                obj = objects_dict[lookup_value]
                obj.evotor_id = detail.get("id")
                obj.save()

    def handle_bulks(self, response):
        """
        Обработка ответа в формате bulk.
        """
        evotor_id = response.get("id")

        if not evotor_id:
            return

        bulk = CRMBulk.objects.get_or_create(evotor_id=evotor_id)[0]
        bulk.status = response.get("status")
        bulk.object_type = response.get("type")
        bulk.save()

        if bulk.status in CRMBulk.FINAL_STATUSES:
            self.finish_bulk(bulk, response)
        else:
            self.create_periodic_task(bulk)

    def finish_bulk(self, bulk, response):
        bulk.date_fineshed = now()
        details = response.get("details")
        if details:
            if bulk.object_type == CRMBulk.PRODUCT:
                self.set_evotor_ids(details, Product, "article")
            elif bulk.object_type == CRMBulk.CATEGORY:
                self.set_evotor_ids(details, Category, "name")

    def create_periodic_task(self, bulk):
        process_bulk_task.apply_async(kwargs={"bulk_evotor_id": bulk.evotor_id, "retry_count": 1}, countdown=10)

    def get_bulk_by_id(self, bulk_id):
        """"
        Получить подробную информацию о состоянии определённой задачи
        GET /bulks/{bulk-id}

        Возвращает подробную информацию о состоянии задачи по её идентификатору.
        """
        endpoint = f"bulks/{bulk_id}"
        return self.send_request(endpoint)

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
            else:
                return {"error": "Invalid"}

            # elif method == "POST":
            #     response = requests.post(url, headers=self.headers, json=data)
            # elif method == "PUT":
            #     response = requests.post(url, headers=self.headers, json=data)
            # elif method == "PATCH":
            #     response = requests.patch(url, headers=self.headers, json=data)
            # elif method == "DELETE":
            #     response = requests.delete(url, headers=self.headers)
            # else:
            #     logger.error(f"Ошибка HTTP запроса. Неизвестный http метод: {method}")
            #     raise ValueError(f"Unsupported HTTP method: {method}")

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


class EvotorStoreClient(EvotorAPICloud):

    # ========= ПОЛУЧЕНИЕ ДАННЫХ

    def get_stores(self):
        """
        Получить список магазинов

        Возвращает массив с информацией о всех магазинах пользователя.
        GET /stores

        Может передать cursor (Если обектов больше 1000)

        ОТВЕТ:
            {
                "items": [
                    {
                    "id": "20170228-F4F1-401B-80FA-9ECCA8451FFB",
                    "name": "Мой магазин",
                    "address": "Россия, г. Москва, ул. Тимура Фрунзе, 24",
                    "user_id": "00-000000000000000",
                    "created_at": "2018-04-17T10:11:49.393+0000",
                    "updated_at": "2018-07-16T16:00:10.663+0000"
                    }
                ],
                "paging": {
                    "next_cursor": "string"
                }
            }
        """
        endpoint = "stores"
        return self.send_request(endpoint)

    def get_terminals(self):
        """
        Получить список смарт-терминалов

        Возвращает массив с информацией о всех смарт-терминалах пользователя
        GET /devices

        Может передать cursor (Если обектов больше 1000)

        ОТВЕТ:
            {
                "items": [
                    {
                    "id": "20170222-D58C-40E0-8051-B53ADFF38860",
                    "name": "Моя касса №1",
                    "store_id": "20170228-F4F1-401B-80FA-9ECCA8451FFB",
                    "timezone_offset": 10800000,
                    "imei": "123456789012345",
                    "firmware_version": "1.2.3",
                    "location": {
                        "lng": 12.34,
                        "lat": 12.34
                    },
                    "user_id": "00-000000000000000",
                    "serial_number":"00307401000000",
                    "model": "POWER",
                    "created_at": "2018-04-17T10:11:49.393+0000",
                    "updated_at": "2018-07-16T16:00:10.663+0000"
                    }
                ],
                "paging": {
                    "next_cursor": "string"
                }
            }
        """
        endpoint = "devices"
        return self.send_request(endpoint)

    # ========= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (РАБОТА С JSON)

    def create_or_update_site_stores(self, stores_json, is_filtered=False):
        error_msgs = []
        try:
            evotor_ids = []
            json_valid = True
            for store_json in stores_json:
                evotor_id = store_json.get("id")
                evotor_ids.append(evotor_id)
                prt, created = Store.objects.get_or_create(evotor_id=evotor_id)
                serializer = StoreSerializer(prt, data=store_json)

                if serializer.is_valid():
                    serializer.save()
                    event_type = CRMEvent.CREATION if created else CRMEvent.UPDATE
                    CRMEvent.objects.create(
                        body="Store created / or updated",
                        sender=CRMEvent.STORE,
                        event_type=event_type,
                    )
                else:
                    json_valid = False
                    logger.error("Ошибка при сериализации %s" % serializer.errors)
                    error_msgs.append(
                        f"Ошибка сериализации магазина: {serializer.errors}"
                    )

            if not json_valid:
                return ", ".join(error_msgs), False

            if not is_filtered:
                for store in Store.objects.all():
                    if store.evotor_id not in evotor_ids:
                        store.evotor_id = None
                        store.save()

        except Exception as e:
            logger.error(f"Ошибка при обновлении магазина: {e}", exc_info=True)
            return f"Ошибка при обновлении магазина: {e}", False

        return "Магазины были успешно обновлены", True

    def create_or_update_site_terminals(self, terminals_json, is_filtered=False):
        error_msgs = []
        try:
            evotor_ids = []
            json_valid = True
            for terminal_json in terminals_json:
                evotor_id = terminal_json.get("id")
                evotor_ids.append(evotor_id)
                trm, created = Terminal.objects.get_or_create(evotor_id=evotor_id)
                serializer = TerminalSerializer(trm, data=terminal_json)

                if serializer.is_valid():
                    serializer.save()
                    event_type = CRMEvent.CREATION if created else CRMEvent.UPDATE
                    CRMEvent.objects.create(
                        body="Store created / or updated",
                        sender=CRMEvent.TERMINAL,
                        event_type=event_type,
                    )
                else:
                    json_valid = False
                    logger.error("Ошибка при сериализации %s" % serializer.errors)
                    error_msgs.append(
                        f"Ошибка сериализации терминалов: {serializer.errors}"
                    )

            if not json_valid:
                return ", ".join(error_msgs), False

            if not is_filtered:
                for terminal in Terminal.objects.all():
                    if terminal.evotor_id not in evotor_ids:
                        terminal.delete()

        except Exception as e:
            logger.error(f"Ошибка при обновлении терминалов: {e}", exc_info=True)
            return f"Ошибка при обновлении терминалов: {e}", False

        return "Терминалы были успешно обновлены", True


class EvotorStaffClient(EvotorAPICloud):

    # ========= ПОЛУЧЕНИЕ ДАННЫХ

    def get_staffs(self):
        """
        Получить список сотрудников

        Возвращает массив с информацией о всех сотрудниках пользователя.
        GET /employees

        Может передать cursor (Если обектов больше 1000)

        ОТВЕТ:
            {
                "items": [
                    {
                    "id": "20170222-5670-4067-8017-FF5F40F1A23E",
                    "name": "Иван",
                    "last_name": "Иванов",
                    "patronymic_name": "Иванович",
                    "phone": 79876543210,
                    "stores": [
                        "20170222-d58c-40e0-8051-b53adff38860"
                    ],
                    "role": "ADMIN",
                    "role_id": "20210630-D4A9-4028-80D3-03EE41907690",
                    "user_id": "00-000000000000000",
                    "created_at": "2018-04-17T10:11:49.393+0000",
                    "updated_at": "2018-07-16T16:00:10.663+0000"
                    }
                ],
                "paging": {
                    "next_cursor": "string"
                }
            }
        """
        endpoint = "employees"
        return self.send_request(endpoint)

    def get_staff_by_id(self, staff_id):
        """
        Получить данные сотрудника по идентификатору

        Возвращает объект с информацией о сотруднике пользователя.
        GET /employees/{employee-id}

        ОТВЕТ:
            {
                "id": "20170222-5670-4067-8017-FF5F40F1A23E",
                "name": "Иван",
                "last_name": "Иванов",
                "patronymic_name": "Иванович",
                "phone": 79876543210,
                "stores": [
                    "20170222-d58c-40e0-8051-b53adff38860"
                ],
                "role": "ADMIN",
                "user_id": "00-000000000000000",
                "created_at": "2018-04-17T10:11:49.393+0000",
                "updated_at": "2018-07-16T16:00:10.663+0000"
            }
        """
        endpoint = f"employees/{staff_id}"
        return self.send_request(endpoint)

    def get_staffs_roles(self):
        """
        Получить список ролей

        Возвращает список всех возможных ролей.
        GET /employees/roles

        Может передать cursor (Если обектов больше 1000)

        ОТВЕТ:
            {
                "items": [
                    {
                    "id": "20200110-CB83-40A7-8037-95DC6E8C51A7",
                    "name": "Администратор"
                    },
                    {
                    "id": "20200110-A68D-40BF-8077-14A012156469",
                    "name": "Кассир"
                    }
                ],
                "paging": {}
            }
        """
        endpoint = "employees/roles"
        return self.send_request(endpoint)

    # ========= ОТПРАВКА ДАННЫХ

    def create_evotor_staff(self, staff):
        """
        Создаёт нового сотрудника с указанной ролью в Эвотор системе.
        Список ролей возвращает метод /employees/roles
        GET /employees

        staff - объект Staff

        ТЕЛО ЗАПРОСА:
            {
                "phone": 79162869949,
                "role_id": "20200817-2BFE-4088-80AF-E095182C5694",
                "name": "Иван",
                "last_name": "Иванович",
                "patronymic_name": "Иванович",
                "stores": [
                    "20190722-EEB1-404D-805D-C911CF2E44EE",
                    "20200221-23D3-40E5-80BD-5EC3ADCDE654",
                    "20190724-6993-408B-80DA-E6799F3759D1"
                ]
            }
        """
        serializer = StaffSerializer(staff)
        staff_json = json.loads(JSONRenderer().render(serializer.data).decode("utf-8"))
        endpoint = "employees"

        response = self.send_request(endpoint, "POST", staff_json)
        error = response.get("error", None) if isinstance(response, dict) else None

        if not error:
            evotor_id = response.get("id", None)
            staff.evotor_id = evotor_id
            staff.save()

        return error

    # ========= СОЗДАНИЕ ЗАПИСЕЙ САЙТА (РАБОТА С JSON)

    def create_or_update_site_roles(self, roles_json, is_filtered=False):
        error_msgs = []
        try:
            evotor_ids = []
            json_valid = True
            for role_json in roles_json:
                name = role_json.get("name")
                role, created = Group.objects.get_or_create(name=name)
                serializer = UserGroupSerializer(role, data=role_json)

                evotor_id = role_json.get("id")
                evotor_ids.append((evotor_id, role.id))

                if serializer.is_valid():
                    serializer.save()
                    event_type = CRMEvent.CREATION if created else CRMEvent.UPDATE
                    CRMEvent.objects.create(
                        body="Role role created / or updated",
                        sender=CRMEvent.STAFF,
                        event_type=event_type,
                    )
                else:
                    json_valid = False
                    logger.error("Ошибка при сериализации %s" % serializer.errors)
                    error_msgs.append(
                        f"Ошибка сериализации роли сотрудника: {serializer.errors}"
                    )

            if not json_valid:
                return ", ".join(error_msgs), False

            if not is_filtered:
                for group_evotor in GroupEvotor.objects.all():
                    if (
                        group_evotor.evotor_id,
                        group_evotor.group_id,
                    ) not in evotor_ids:
                        group_evotor.delete()

        except Exception as e:
            logger.error(f"Ошибка при обновлении ролей персонала: {e}")
            return f"Ошибка при обновлении ролей персонала: {e}", False

        return "Роли сотрудников были успешно обновлены", True

    def create_or_update_site_staffs(self, staffs_json, is_filtered=False):
        error_msgs = []
        staffs = Staff.objects.all()
        try:
            evotor_ids = []
            json_valid = True
            created = False
            for staff_json in staffs_json:
                evotor_id = staff_json.get("id")
                evotor_ids.append(evotor_id)
                try:
                    staff = staffs.get(evotor_id=evotor_id)
                    serializer = StaffSerializer(staff, data=staff_json)
                except Staff.DoesNotExist:
                    created = True
                    serializer = StaffSerializer(data=staff_json)

                if serializer.is_valid():
                    serializer.save()
                    event_type = CRMEvent.CREATION if created else CRMEvent.UPDATE
                    CRMEvent.objects.create(
                        body="Staff created / or updated",
                        sender=CRMEvent.STAFF,
                        event_type=event_type,
                    )
                else:
                    json_valid = False
                    logger.error("Ошибка при сериализации %s" % serializer.errors)
                    error_msgs.append(
                        f"Ошибка сериализации сотрудника: {serializer.errors}"
                    )

            if not json_valid:
                return ", ".join(error_msgs), False

            if not is_filtered:
                for staff in staffs:
                    if staff.evotor_id not in evotor_ids:
                        staff.evotor_id = None
                        staff.save()

        except Exception as e:
            logger.error(f"Ошибка при обновлении списка сотрудников: {e}")
            return f"Ошибка при обновлении списка сотрудников: {e}", False

        return "Сотрудники были успешно обновлены", True


class EvotorGroupClient(EvotorAPICloud):

    # ========= ПОЛУЧЕНИЕ ДАННЫХ (НЕ ВЫЗЫВАЕМ)

    def get_groups(self, store_id):
        """
        Получить все группы товаров или модификаций

        Возвращает все группы товаров из магазина.
        GET /stores/{store-id}/product-groups

        ОТВЕТ:
            {
                "items": [
                    {
                    "parent_id": "1ddea16b-971b-dee5-3798-1b29a7aa2e27",
                    "name": "Группа",
                    "store_id": "20180820-7052-4047-807D-E82C50000000",
                    "user_id": "00-000000000000000",
                    "created_at": "2018-09-11T16:18:35.397+0000",
                    "updated_at": "2018-09-11T16:18:35.397+0000",
                    "barcodes": [
                        "2000000000060"
                    ],
                    "attributes": [
                        {
                        "id": "36755a25-8f56-11e8-96a6-85f64fd5f8e3",
                        "name": "Цвет",
                        "choices": [
                            {
                            "id": "36755a27-8f56-11e8-96a6-85f64fd5f8e3",
                            "name": "Зелёный"
                            }
                        ]
                        }
                    ]
                    }
                ],
                "paging": {
                    "next_cursor": "string"
                }
            }
        """
        endpoint = f"stores/{store_id}/product-groups"
        return self.send_request(endpoint)

    # ========= ОТПРАВКА ДАННЫХ (НЕ ВЫЗЫВАЕМ)

    def send_evotor_group(self, group, store_id):
        """
        Создать/заменить несколько групп товаров или модификаций

        Создаёт или заменяет группы товаров или группы модификаций товаров в магазине.
        Идентификаторы объектов формирует клиент API.

        PUT /stores/{store-id}/product-groups

        Чтобы передать несколько объектов дополните заголовок Content-Type модификатором +bulk.

        Количество модификаций в группе может быть от 0 до 200, каждая модификация может содержать до 500 атрибутов.

        ТЕЛО:
        [
            {
                "parent_id": "1ddea16b-971b-dee5-3798-1b29a7aa2e27",
                "name": "Группа",
                "barcodes": [
                "2000000000060"
                ],
                "attributes": [
                {
                    "id": "36755a25-8f56-11e8-96a6-85f64fd5f8e3",
                    "name": "Цвет",
                    "choices": [
                    {
                        "id": "36755a27-8f56-11e8-96a6-85f64fd5f8e3",
                        "name": "Зелёный"
                    }
                    ]
                }
                ]
            }
        ]

        ОТВЕТ:
        {
            "id": "ca187ddc-8d1b-4d0e-b20d-c509082da528",
            "modified_at": "2018-01-01T00:00:00.000Z",
            "status": "COMPLETED",
            "type": "product",
            "details": [
                {    }
            ]
        }
        """
        serializer = ProductGroupsSerializer(group, context={"store_id": store_id})
        group_json = json.loads(JSONRenderer().render(serializer.data).decode("utf-8"))

        endpoint = f"stores/{store_id}/product-groups"
        response = self.send_request(endpoint, "PUT", group_json)
        error = response.get("error", None) if isinstance(response, dict) else None

        if not error:
            group.evotor_id = response.get("id")
            group.save()

        return error

    def send_evotor_groups(self, groups, store_id):
        """
        Создать/заменить несколько групп товаров или модификаций

        Создаёт или заменяет группы товаров или группы модификаций товаров в магазине.
        Идентификаторы объектов формирует клиент API.

        PUT /stores/{store-id}/product-groups

        Чтобы передать несколько объектов дополните заголовок Content-Type модификатором +bulk.

        Количество модификаций в группе может быть от 0 до 200, каждая модификация может содержать до 500 атрибутов.

        ТЕЛО:
        [
            {
                "parent_id": "1ddea16b-971b-dee5-3798-1b29a7aa2e27",
                "name": "Группа",
                "barcodes": [
                "2000000000060"
                ],
                "attributes": [
                {
                    "id": "36755a25-8f56-11e8-96a6-85f64fd5f8e3",
                    "name": "Цвет",
                    "choices": [
                    {
                        "id": "36755a27-8f56-11e8-96a6-85f64fd5f8e3",
                        "name": "Зелёный"
                    }
                    ]
                }
                ]
            }
        ]

        ОТВЕТ:
        {
            "id": "ca187ddc-8d1b-4d0e-b20d-c509082da528",
            "modified_at": "2018-01-01T00:00:00.000Z",
            "status": "COMPLETED",
            "type": "product",
            "details": [
                {    }
            ]
        }
        """

        if len(groups) == 1:
            return self.send_evotor_group(groups[0], store_id)

        serializer = ProductGroupsSerializer(
            {"items": groups}, context={"store_id": store_id}
        )
        groups_json = json.loads(
            JSONRenderer().render(serializer.data.get("items")).decode("utf-8")
        )

        endpoint = f"stores/{store_id}/product-groups"
        response = self.send_request(endpoint, "PUT", groups_json, True)
        error = response.get("error", None) if isinstance(response, dict) else None

        if not error:
            self.handle_bulks(response)

        return error

    # ========= СОЗДАНИЕ ЗАПИСЕЙ ЭВОТОР (ВЫЗЫВАЕМ)

    def update_or_create_evotor_group(self, group):
        """
        Создаёт или заменяет в магазине одину группу товаров или модификаций.
        """
        return self.update_or_create_evotor_groups([group])

    def update_or_create_evotor_groups(self, groups):
        """
        Создаёт или заменяет товары или модификации товаров в магазине.
        Идентификаторы объектов формирует клиент API.
        """
        errors = []
        groups_filtered = defaultdict(list)
        evotor_store_ids = []

        for group in groups:
            if isinstance(group, Product):
                if group.is_parent:
                    store_ids = set()
                    for child in group.children.all():
                        for stockrecord in child.stockrecords.all():
                            store_id = stockrecord.store.evotor_id
                            store_ids.add(store_id)
                    for store_id in store_ids:
                        groups_filtered[store_id].append(group)
            else:
                if not evotor_store_ids:
                    evotor_store_ids = Store.objects.filter(is_active=True).values_list(
                        "evotor_id", flat=True
                    )
                for store_id in evotor_store_ids:
                    groups_filtered[store_id].append(group)

        for store_id, groups_by_store in groups_filtered.items():
            error = self.send_evotor_groups(groups_by_store, store_id)
            if error:
                errors.append(error)

        return ", ".join(errors)

    def delete_evotor_group(self, group):
        """
        Удалить группу товаров или модификаций

        Удаляет из магазина группу с указанным идентификатором.
        DELETE /stores/{store-id}/product-groups/{product-group-id}
        """
        errors = []
        if group.evotor_id:
            if isinstance(group, Product):
                store_ids = set()
                if group.is_parent:
                    for child in group.children.all():
                        for stockrecord in child.stockrecords.all():
                            store_id = stockrecord.store.evotor_id
                            if store_id:
                                store_ids.add(store_id)
            else:
                store_ids = Store.objects.filter(is_active=True).values_list(
                    "evotor_id", flat=True
                )

            for store_id in store_ids:
                endpoint = f"stores/{store_id}/product-groups/{group.evotor_id}"
                response = self.send_request(endpoint, "DELETE")
                self.handle_response_errors(response, errors)
        else:
            errors.append(
                f"Категория или родительский товар - {group.get_name()} не имеет идентификатора Эвотор"
            )

        return ", ".join(errors)

    def delete_evotor_groups(self, groups):
        """
        Удаляет группы товаров или модификаций товаров из магазина
        DELETE /stores/{store-id}/product-groups

        Чтобы удалить несколько групп, в параметре id, укажите через запятую идентификаторы групп к удалению.
        В рамках одного запроса можно удалить до 100 групп.

        """
        errors = []
        groups_to_delete = defaultdict(list)
        evotor_store_ids = []

        for group in groups:
            if group.evotor_id:
                if isinstance(group, Product):
                    if group.is_parent:
                        store_ids = set()
                        for child in group.children.all():
                            for stockrecord in child.stockrecords.all():
                                store_id = stockrecord.store.evotor_id
                                store_ids.add(store_id)
                        for store_id in store_ids:
                            groups_to_delete[store_id].append(group)
                else:
                    if not evotor_store_ids:
                        evotor_store_ids = Store.objects.filter(
                            is_active=True
                        ).values_list("evotor_id", flat=True)
                    for store_id in evotor_store_ids:
                        groups_to_delete[store_id].append(group)
            else:
                errors.append(
                    f"Категория или родительский товар - {group.get_name()} не имеет идентификатора Эвотор"
                )

        for store_id, group_to_delete in groups_to_delete.items():
            endpoint = f"stores/{store_id}/product-groups/?{','.join(group_to_delete.evotor_id)}"
            response = self.send_request(endpoint, "DELETE")
            self.handle_response_errors(response, errors)

        return ", ".join(errors)

    # ========= СОЗДАНИЕ ЗАПИСЕЙ САЙТА (РАБОТА С JSON)

    def create_or_update_site_groups(self, groups_json, is_filtered=False):
        error_msgs = []
        try:
            evotor_ids = []
            json_valid = True
            for group_json in groups_json:
                evotor_id = group_json.get("id")
                evotor_ids.append(evotor_id)
                attributes = group_json.get("attributes")
                if attributes:
                    try:
                        instance = Product.objects.get(evotor_id=evotor_id)
                    except Product.DoesNotExist:
                        instance = None
                else:
                    try:
                        instance = Category.objects.get(evotor_id=evotor_id)
                    except Category.DoesNotExist:
                        instance = None

                if instance:
                    serializer = ProductGroupSerializer(instance, data=group_json)
                    created = False
                else:
                    serializer = ProductGroupSerializer(data=group_json)
                    created = True

                if serializer.is_valid():
                    if not AdditionalCategory.objects.filter(evotor_id=evotor_id).exists():
                        group = serializer.save()
                        event_type = CRMEvent.CREATION if created else CRMEvent.UPDATE
                        CRMEvent.objects.create(
                            body=f"ProductGroup created / or updated - { group.name }",
                            sender=CRMEvent.GROUP,
                            event_type=event_type,
                        )
                else:
                    json_valid = False
                    logger.error("Ошибка при сериализации %s" % serializer.errors)
                    error_msgs.append(
                        f"Ошибка сериализации группы товаров или модификации товаров: {serializer.errors}"
                    )

            if not json_valid:
                return ", ".join(error_msgs), False

            if not is_filtered:
                for category in Category.objects.all():
                    if category.evotor_id not in evotor_ids:
                        category.evotor_id = None
                        category.save()

        except Exception as e:
            logger.error(
                f"Ошибка при обновлении группы товаров или модификации товаров: {e}",
                exc_info=True,
            )
            return (
                f"Ошибка при обновлении группы товаров или модификации товаров: {e}",
                False,
            )

        return "Группы товаров и модификаций были успешно обновлены", True


class EvotorProductClient(EvotorGroupClient):
    """ "
    Работа с вариативными товарами
    https://developer.evotor.ru/docs/rest_product_modifications_guide.html
    """

    # ========= ПОЛУЧЕНИЕ ДАННЫХ (НЕ ВЫЗЫВАЕМ)

    def get_products(self, store_id):
        """
        Получить все товары

        Возвращает все товары и модификации товаров из магазина.
        GET /stores/{store-id}/products

        ОТВЕТ:
            {
                "items": [
                    {
                    "parent_id": "1ddea16b-971b-dee5-3798-1b29a7aa2e27",
                    "name": "Сидр",
                    "is_excisable": true,
                    "measure_name": "шт",
                    "tax": "VAT_18",
                    "allow_to_sell": true,
                    "price": 123.12,
                    "description": "Вкусный яблочный сидр",
                    "article_number": "СДР-ЯБЛЧ",
                    "code": "42",
                    "barcodes": [
                        "2000000000060"
                    ],
                    "type": "ALCOHOL_NOT_MARKED",
                    "id": "01ba18b6-8707-5f47-3d9c-4db058054cb3",
                    "store_id": "20180820-7052-4047-807D-E82C50000000",
                    "user_id": "00-000000000000000",
                    "created_at": "2018-09-11T16:18:35.397+0000",
                    "updated_at": "2018-09-11T16:18:35.397+0000"
                    }
                ],
                "paging": {
                    "next_cursor": "string"
                }
            }
        """
        endpoint = f"stores/{store_id}/products"
        return self.send_request(endpoint)

    def get_primary_products(self, store_id):
        """
        Получить все основные товары
        """
        all_products = self.get_products(store_id)
        items = all_products.get("items", None)

        if items:
            additional_categories = AdditionalCategory.objects.values_list("evotor_id")
            filtered_items = [
                item for item in items if item.get("parent_id") not in additional_categories
            ]
            all_products["items"] = filtered_items
            return all_products

        return all_products

    # ========= ОТПРАВКА ДАННЫХ (НЕ ВЫЗЫВАЕМ)

    def send_evotor_product(self, product, store_id):
        """
        Обновить данные товара

        Создаёт или заменяет в магазине один товар или модификацию товара с указанным идентификатором.
        PATCH /stores/{store-id}/products/{product-id}

        Обновляет цену, закупочную цену и остатки товара или модификации товара в магазине.
        Вы можете обновить как один, так и несколько параметров.
        Запрос не может быть пустым.

        product - объект Product

        ТЕЛО:
            {
            "quantity": 12,
            "cost_price": 100.123,
            "price": 123.12
            }

        ОТВЕТ:
            {
                "parent_id": "1ddea16b-971b-dee5-3798-1b29a7aa2e27",
                "name": "Сидр",
                "measure_name": "шт",
                "tax": "VAT_18",
                "allow_to_sell": true,
                "price": 123.12,
                "description": "Вкусный яблочный сидр",
                "article_number": "СДР-ЯБЛЧ",
                "code": "42",
                "barcodes": [
                    "2000000000060"
                ],
                "type": "ALCOHOL_NOT_MARKED",
                "id": "01ba18b6-8707-5f47-3d9c-4db058054cb2",
                "quantity": 12,
                "cost_price": 100.123,
                "attributes_choices": {},
                "store_id": "string",
                "user_id": "string",
                "created_at": "string",
                "updated_at": "string"
            }
        """

        serializer = ProductSerializer(product, context={"store_id": store_id})
        product_json = json.loads(JSONRenderer().render(serializer.data).decode("utf-8"))

        endpoint = f"stores/{store_id}/products"
        response = self.send_request(endpoint, "PUT", product_json)
        error = response.get("error", None) if isinstance(response, dict) else None

        if not error:
            product.evotor_id = response.get("id")
            product.save()

        return error

    def send_evotor_products(self, products, store_id):
        """
        Обновить данные товара

        Создаёт или заменяет в магазине один товар или модификацию товара с указанным идентификатором.
        PATCH /stores/{store-id}/products/{product-id}

        Обновляет цену, закупочную цену и остатки товара или модификации товара в магазине.
        Вы можете обновить как один, так и несколько параметров.
        Запрос не может быть пустым.

        product - объект Product

        ТЕЛО:
            {
            "quantity": 12,
            "cost_price": 100.123,
            "price": 123.12
            }

        ОТВЕТ:
            {
                "parent_id": "1ddea16b-971b-dee5-3798-1b29a7aa2e27",
                "name": "Сидр",
                "measure_name": "шт",
                "tax": "VAT_18",
                "allow_to_sell": true,
                "price": 123.12,
                "description": "Вкусный яблочный сидр",
                "article_number": "СДР-ЯБЛЧ",
                "code": "42",
                "barcodes": [
                    "2000000000060"
                ],
                "type": "ALCOHOL_NOT_MARKED",
                "id": "01ba18b6-8707-5f47-3d9c-4db058054cb2",
                "quantity": 12,
                "cost_price": 100.123,
                "attributes_choices": {},
                "store_id": "string",
                "user_id": "string",
                "created_at": "string",
                "updated_at": "string"
            }
        """
        self.create_products_parent(products, store_id)

        if len(products) == 1:
            return self.send_evotor_product(products[0], store_id)

        serializer = ProductsSerializer(
            {"items": products}, context={"store_id": store_id}
        )
        products_json = json.loads(
            JSONRenderer().render(serializer.data.get("items")).decode("utf-8")
        )

        endpoint = f"stores/{store_id}/products"
        response = self.send_request(endpoint, "PUT", products_json, True)
        error = response.get("error", None) if isinstance(response, dict) else None

        if not error:
            self.handle_bulks(response)

        return error

    def create_products_parent(self, products, store_id):
        errors = []
        groups = set()
        parents = set()
        for product in products:
            parent_id = product.get_evotor_parent_id()
            if not parent_id:
                if product.is_child:
                    parent = product.parent
                    if not parent.evotor_id:
                        parents.add(parent)

                    parent_parent_id = parent.get_evotor_parent_id()
                    if not parent_parent_id:
                        category = parent.categories.first()
                        if category:
                            groups.add(category)
                else:
                    category = product.categories.first()
                    if category:
                        groups.add(category)

        if groups:
            errors_groups = self.send_evotor_groups(list(groups), store_id)
            if errors_groups:
                errors.append(errors_groups)

        if parents:
            errors_parents = self.send_evotor_groups(list(parents), store_id)
            if errors_parents:
                errors.append(errors_parents)

        return " ".join(errors)

    # === СОЗДАНИЕ ЗАПИСЕЙ ЭВОТОР (ВЫЗЫВАЕМ)

    def update_or_create_evotor_product(self, product):
        """
        Создаёт или заменяет в магазине один товар или модификацию товара..
        """
        return self.update_or_create_evotor_products([product])

    def update_or_create_evotor_products(self, products):
        """
        Создаёт или заменяет товары или модификации товаров в магазине.
        Идентификаторы объектов формирует клиент API.
        """
        errors = []
        groups_filtered = defaultdict(list)
        products_filtered = defaultdict(list)

        for product in products:
            if product.is_parent:
                store_ids = set()
                for child in product.children.all():
                    for stockrecord in child.stockrecords.all():
                        store_id = stockrecord.store.evotor_id
                        if store_id:
                            store_ids.add(store_id)
                for store_id in store_ids:
                    groups_filtered[store_id].append(product)
            else:
                for stockrecord in product.stockrecords.all():
                    store_id = stockrecord.store.evotor_id
                    if store_id:
                        products_filtered[store_id].append(product)

        for store_id, groups_by_store in groups_filtered.items():
            error = self.send_evotor_groups(groups_by_store, store_id)
            if error:
                errors.append(error)

        for store_id, products_by_store in products_filtered.items():
            error = self.send_evotor_products(products_by_store, store_id)
            if error:
                errors.append(error)

        return ", ".join(errors)

    def update_evotor_stockrecord(self, product):
        """
        Обновить данные товара

        Создаёт или заменяет в магазине один товар или модификацию товара с указанным идентификатором.
        PATCH /stores/{store-id}/products/{product-id}

        Обновляет цену, закупочную цену и остатки товара или модификации товара в магазине.
        Вы можете обновить как один, так и несколько параметров.
        Запрос не может быть пустым.

        product - объект Product

        ТЕЛО:
            {
            "quantity": 12,
            "cost_price": 100.123,
            "price": 123.12
            }

        ОТВЕТ:
            {
                "parent_id": "1ddea16b-971b-dee5-3798-1b29a7aa2e27",
                "name": "Сидр",
                "measure_name": "шт",
                "tax": "VAT_18",
                "allow_to_sell": true,
                "price": 123.12,
                "description": "Вкусный яблочный сидр",
                "article_number": "СДР-ЯБЛЧ",
                "code": "42",
                "barcodes": [
                    "2000000000060"
                ],
                "type": "ALCOHOL_NOT_MARKED",
                "id": "01ba18b6-8707-5f47-3d9c-4db058054cb2",
                "quantity": 12,
                "cost_price": 100.123,
                "attributes_choices": {},
                "store_id": "string",
                "user_id": "string",
                "created_at": "string",
                "updated_at": "string"
            }
        """
        errors = []
        product_id = product.evotor_id

        if product_id:
            for stockrecord in product.stockrecords.all():
                store_id = stockrecord.store.evotor_id
                if store_id:
                    stockrecord_json = {
                        "quantity": stockrecord.num_in_stock or 0,
                        "cost_price": (
                            float(stockrecord.cost_price)
                            if stockrecord.cost_price is not None
                            else 0
                        ),
                        "price": (
                            float(stockrecord.price)
                            if stockrecord.price is not None
                            else 0
                        ),
                    }
                    endpoint = f"stores/{store_id}/products/{product_id}"
                    response = self.send_request(endpoint, "PATCH", stockrecord_json)

                    self.handle_response_errors(response, errors)
        else:
            errors.append(f"Товар {product.get_name()} не имеет идентификатора Эвотор")

        return ", ".join(errors)

    def delete_evotor_product_by_store(self, product, store_id):
        """
        Удалить товар или модификацию товара

        Удаляет из магазина товар или модификацию товара с указанным идентификатором.
        DELETE /stores/{store-id}/products/{product-id}

        product_id - строка ID Products

        """
        errors = []

        product_id = product.evotor_id
        if product_id:
            endpoint = f"stores/{store_id}/products/{product_id}"
            response = self.send_request(endpoint, "DELETE")

            self.handle_response_errors(response, errors)
        else:
            errors.append(f"Товар {product.get_name()} не имеет идентификатора Эвотор")

        return ", ".join(errors)

    def delete_evotor_product(self, product):
        """
        Удалить товар или модификацию товара

        Удаляет из магазина товар или модификацию товара с указанным идентификатором.
        DELETE /stores/{store-id}/products/{product-id}

        product_id - строка ID Products

        """
        errors = []

        if product.is_parent:
            # подразумевается, что удаление модификации влечет удаление дочерних элементов
            return self.delete_evotor_group(product)

        product_id = product.evotor_id
        if product_id:
            for stockrecord in product.stockrecords.all():
                store_id = stockrecord.store.evotor_id
                if store_id:
                    endpoint = f"stores/{store_id}/products/{product_id}"
                    response = self.send_request(endpoint, "DELETE")

                    self.handle_response_errors(response, errors)
        else:
            errors.append(f"Товар {product.get_name()} не имеет идентификатора Эвотор")

        return ", ".join(errors)

    def delete_evotor_products(self, products):
        """
        Удалить несколько товаров или модификаций товаров данные товара
        DELETE /stores/{store-id}/products

        Удаляет товары и модификации товаров из магазина.
        Чтобы удалить несколько товаров, в параметре id, укажите через запятую идентификаторы товаров к удалению.
        В рамках одного запроса можно удалить до 100 товаров.

        products - список ID Products

        """
        products_to_delete = {}
        groups_to_delete = []
        errors = []

        for product in products:
            if product.is_parent:
                groups_to_delete.append(product)
                # подразумевается, что удаление модификации влечет удаление дочерних элементов
            else:
                product_id = product.evotor_id
                if product_id:
                    for stockrecord in product.stockrecords.all():
                        store_id = stockrecord.store.evotor_id
                        if store_id:
                            products_to_delete[store_id].append(product_id)

        self.delete_evotor_groups(groups_to_delete)

        for store_id, product_ids in products_to_delete.items():
            endpoint = f"stores/{store_id}/products/?{','.join(product_ids)}"
            response = self.send_request(endpoint, "DELETE")

            self.handle_response_errors(response, errors)

        return ", ".join(errors)

    # ========= СОЗДАНИЕ ЗАПИСЕЙ САЙТА (РАБОТА С JSON)

    def create_or_update_site_products(self, products_json, is_filtered=False):
        error_msgs = []
        products = Product.objects.all()
        addit_parent_ids = AdditionalCategory.objects.values_list("evotor_id", flat=True)
        try:
            evotor_ids = []
            json_valid = True
            created = False
            for product_json in products_json:
                evotor_id = product_json.get("id")
                evotor_ids.append(evotor_id)
                try:
                    prd = products.get(evotor_id=evotor_id)
                    serializer = ProductSerializer(prd, data=product_json)
                except Product.DoesNotExist:
                    created = True
                    serializer = ProductSerializer(data=product_json)

                if serializer.is_valid():
                    parent_id = product_json.get("parent_id")
                    is_additional = parent_id in addit_parent_ids

                    if not is_additional:
                        product = serializer.save()
                        event_type = CRMEvent.CREATION if created else CRMEvent.UPDATE
                        CRMEvent.objects.create(
                            body=f"Product created / updated - { product.name }",
                            sender=CRMEvent.PRODUCT,
                            event_type=event_type,
                        )
                else:
                    json_valid = False
                    logger.error("Ошибка при сериализации %s" % serializer.errors)
                    error_msgs.append(
                        f"Ошибка сериализации товара: {serializer.errors}"
                    )

            if not json_valid:
                return ", ".join(error_msgs), False

            if not is_filtered:
                for product in products:
                    if product.evotor_id not in evotor_ids:
                        product.evotor_id = None
                        product.save()

        except Exception as e:
            logger.error(f"Ошибка при обновлении товара: {e}", exc_info=True)
            return f"Ошибка при обновлении товара: {e}", False

        return "Товары были успешно обновлены", True


class EvotorAdditionalClient(EvotorProductClient):

    # ========= ПОЛУЧЕНИЕ ДАННЫХ (НЕ ВЫЗЫВАЕМ)

    def get_additionals_products(self, store_id):
        """
        Получить все дополнительные товары
        """
        all_products = self.get_products(store_id)
        items = all_products.get("items", None)

        if items:
            additional_categories = AdditionalCategory.objects.values_list("evotor_id")
            filtered_items = [
                item for item in items if item.get("parent_id") in additional_categories
            ]
            all_products["items"] = filtered_items
            return all_products

        return all_products

    # ========= ОТПРАВКА ДАННЫХ (НЕ ВЫЗЫВАЕМ)

    def send_evotor_additional(self, additional, store_id):
        """
        Создать или изменить доп. товар
        """

        serializer = AdditionalsSerializer(additional, context={"store_id": store_id})
        additional_json = json.loads(JSONRenderer().render(serializer.data).decode("utf-8"))

        endpoint = f"stores/{store_id}/products"
        response = self.send_request(endpoint, "PUT", additional_json)
        error = response.get("error", None) if isinstance(response, dict) else None

        if not error:
            additional.evotor_id = response.get("id")
            additional.save()

        return error

    def send_evotor_additionals(self, additionals, store_id):
        """
        Создать или изменить доп. товар
        """

        if len(additionals) == 1:
            return self.send_evotor_additional(additionals[0], store_id)

        serializer = AdditionalsSerializer(
            {"items": additionals}, context={"store_id": store_id}
        )
        additionals_json = json.loads(
            JSONRenderer().render(serializer.data.get("items")).decode("utf-8")
        )

        endpoint = f"stores/{store_id}/products"
        response = self.send_request(endpoint, "PUT", additionals_json, True)
        error = response.get("error", None) if isinstance(response, dict) else None

        if not error:
            self.handle_bulks(response)

        return error

    # ========= СОЗДАНИЕ ЗАПИСЕЙ ЭВОТОР (ВЫЗЫВАЕМ)

    def update_or_create_evotor_additional(self, additional):
        """
        Создаёт или заменяет в магазине один доп товар
        """
        return self.update_or_create_evotor_additionals([additional])

    def update_or_create_evotor_additionals(self, additionals):
        """
        Создаёт или заменяет доп товары в магазине.
        Идентификаторы объектов формирует клиент API.
        """
        errors = []
        additionals_filtered = defaultdict(list),

        active_stores = Store.objects.filter(is_active=True).values_list("id", "evotor_id")
        existing_categories = set(
            AdditionalCategory.objects.values_list("store_id", flat=True)
        )

        for store_id, store_evotor_id in active_stores:
            if store_id not in existing_categories:
                endpoint = f"stores/{store_evotor_id}/product-groups/"
                response = self.send_request(endpoint, "PUT", {"name": "Дополнительные товары"})
                error = response.get("error") if isinstance(response, dict) else None
                if error:
                    errors.append(error)
                else:
                    AdditionalCategory.objects.create(
                        store_id=store_id,
                        evotor_id=response.get("id"),
                    )

        for additional in additionals:
            for store in additional.stores.filter(is_active=True):
                store_id = store.evotor_id
                if store_id:
                    additionals_filtered[store_id].append(additional)

        for store_id, additionals_by_store in additionals_filtered.items():
            error = self.send_evotor_additionals(
                additionals_by_store, store_id
            )
            if error:
                errors.append(error)

        return ", ".join(errors)

    def delete_evotor_additional_by_store(self, additional, store_id):
        """
        Удалить товар или модификацию товара

        Удаляет из магазина товар или модификацию товара с указанным идентификатором.
        DELETE /stores/{store-id}/products/{product-id}

        product_id - строка ID Products

        """
        errors = []

        additional_id = additional.evotor_id
        if additional_id:
            endpoint = f"stores/{store_id}/products/{additional_id}"
            response = self.send_request(endpoint, "DELETE")

            self.handle_response_errors(response, errors)
        else:
            errors.append(f"Товар {additional.get_name()} не имеет идентификатора Эвотор")

        return ", ".join(errors)

    def delete_evotor_additional(self, additional):
        """
        Удалить товар или модификацию товара

        Удаляет из магазина товар или модификацию товара с указанным идентификатором.
        DELETE /stores/{store-id}/products/{product-id}

        product_id - строка ID Products

        """
        errors = []

        additional_id = additional.evotor_id
        if additional_id:
            for store in additional.stores.all():
                store_id = store.evotor_id
                if store_id:
                    endpoint = f"stores/{store_id}/products/{additional_id}"
                    response = self.send_request(endpoint, "DELETE")

                    self.handle_response_errors(response, errors)
        else:
            errors.append(f"Товар {additional.get_name()} не имеет идентификатора Эвотор")

        return ", ".join(errors)

    def delete_evotor_additionals(self, additionals):
        """
        Удалить несколько товаров или модификаций товаров данные товара
        DELETE /stores/{store-id}/products

        Удаляет товары и модификации товаров из магазина.
        Чтобы удалить несколько товаров, в параметре id, укажите через запятую идентификаторы товаров к удалению.
        В рамках одного запроса можно удалить до 100 товаров.

        products - список ID Products

        """
        additionals_to_delete = {}
        errors = []

        for additional in additionals:
            additional_id = additional.evotor_id
            if additional_id:
                for store in additional.stores.all():
                    store_id = store.evotor_id
                    if store_id:
                        additionals_to_delete[store_id].append(additional_id)

        for store_id, additional_ids in additionals_to_delete.items():
            endpoint = f"stores/{store_id}/products/?{','.join(additional_ids)}"
            response = self.send_request(endpoint, "DELETE")

            self.handle_response_errors(response, errors)

        return ", ".join(errors)


    # ========= СОЗДАНИЕ ЗАПИСЕЙ САЙТА (РАБОТА С JSON)

    def create_or_update_site_additionals(self, additionals_json, is_filtered=False):
        error_msgs = []
        additionals = Additional.objects.all()
        try:
            evotor_ids = []
            json_valid = True
            created = False
            for additional_json in additionals_json:
                evotor_id = additional_json.get("id")
                evotor_ids.append(evotor_id)
                try:
                    addit = additionals.get(evotor_id=evotor_id)
                    serializer = AdditionalSerializer(addit, data=additional_json)
                except Product.DoesNotExist:
                    created = True
                    serializer = AdditionalSerializer(data=additional_json)

                if serializer.is_valid():
                    additional = serializer.save()
                    event_type = CRMEvent.CREATION if created else CRMEvent.UPDATE
                    CRMEvent.objects.create(
                        body=f"Additional created / updated - { additional.name }",
                        sender=CRMEvent.PRODUCT,
                        event_type=event_type,
                    )
                else:
                    json_valid = False
                    logger.error("Ошибка при сериализации %s" % serializer.errors)
                    error_msgs.append(
                        f"Ошибка сериализации товара: {serializer.errors}"
                    )

            if not json_valid:
                return ", ".join(error_msgs), False

            if not is_filtered:
                for additional in additionals:
                    if additional.evotor_id not in evotor_ids:
                        additional.evotor_id = None
                        additional.save()

        except Exception as e:
            logger.error(
                f"Ошибка при обновлении дополнительного товара: {e}", exc_info=True
            )
            return f"Ошибка при обновлении дополнительного товара: {e}", False

        return "Дополнительные товары были успешно обновлены", True


# делаем EvotorDocClient и EvotorPushNotifClient


class EvotorDocClient(EvotorAPICloud):

    # ========= ПОЛУЧЕНИЕ ДАННЫХ

    def get_docs(self, store_id):
        """
        Получить список документов

        Возвращает массив документов
        GET /stores/{store-id}/documents

        Все доку разные. Смотри ссылку
        https://developer.evotor.ru/docs/rest_api_get_store_documents.html

        Может передать cursor (Если обектов больше 1000)

        ОТВЕТ:
            {
                "items": [
                    {
                    "type": "OPEN_SESSION",
                    "id": "20170222-D58C-40E0-8051-B53ADFF38860",
                    "extras": {},
                    "number": 1234,
                    "close_date": "2017-01-10T09:33:19.757+0000",
                    "time_zone_offset": 10800000,
                    "session_id": "1022722e-9441-4beb-beae-c6bc5e7af30d",
                    "session_number": 80,
                    "close_user_id": "20170417-46B8-40B9-802E-4DEB67C07565",
                    "device_id": "20170928-9441-4BEB-BEAE-C6BC5E7AF30D",
                    "store_id": "20170928-3176-40EB-80E2-A11F032E282A",
                    "user_id": "09-012345678901234",
                    "version": "V2",
                    "body": {}
                    }
                ],
                "paging": {
                    "next_cursor": "string"
                }
            }
        """
        endpoint = f"stores/{store_id}/documents"
        return self.send_request(endpoint)

    def get_doc_by_id(self, store_id, doc_id):
        """
        Получить документ по идентификатору

        Возвращает документ с указанным идентификатором
        GET /stores/{store-id}/documents/{document-id}

        ОТВЕТ:
            {
            "type": "OPEN_SESSION",
            "id": "20170222-D58C-40E0-8051-B53ADFF38860",
            "extras": {},
            "number": 1234,
            "close_date": "2017-01-10T09:33:19.757+0000",
            "time_zone_offset": 10800000,
            "session_id": "1022722e-9441-4beb-beae-c6bc5e7af30d",
            "session_number": 80,
            "close_user_id": "20170417-46B8-40B9-802E-4DEB67C07565",
            "device_id": "20170928-9441-4BEB-BEAE-C6BC5E7AF30D",
            "store_id": "20170928-3176-40EB-80E2-A11F032E282A",
            "user_id": "09-012345678901234",
            "version": "V2",
            "body": {}
            }
        """
        endpoint = f"stores/{store_id}/documents/{doc_id}"
        return self.send_request(endpoint)

    def get_docs_by_terminal_id(self, store_id, terminal_id):
        """
        Получить список документов по идентификатору смарт-терминала

        Получить список документов по идентификатору смарт-терминала
        GET /stores/{store-id}/devices/{device-id}/documents

        Может передать cursor (Если обектов больше 1000)

        ОТВЕТ:
            {
                "items": [
                    {
                    "type": "OPEN_SESSION",
                    "id": "20170222-D58C-40E0-8051-B53ADFF38860",
                    "extras": {},
                    "number": 1234,
                    "close_date": "2017-01-10T09:33:19.757+0000",
                    "time_zone_offset": 10800000,
                    "session_id": "1022722e-9441-4beb-beae-c6bc5e7af30d",
                    "session_number": 80,
                    "close_user_id": "20170417-46B8-40B9-802E-4DEB67C07565",
                    "device_id": "20170928-9441-4BEB-BEAE-C6BC5E7AF30D",
                    "store_id": "20170928-3176-40EB-80E2-A11F032E282A",
                    "user_id": "09-012345678901234",
                    "version": "V2",
                    "body": {}
                    }
                ],
                "paging": {
                    "next_cursor": "string"
                }
            }
        """
        endpoint = f"stores/{store_id}/devices/{terminal_id}/documents"
        return self.send_request(endpoint)

    # ========= СОЗДАНИЕ ЗАПИСЕЙ САЙТА (РАБОТА С JSON)

    def create_or_update_site_order(self, order_json):
        error_msgs = []
        orders = Order.objects.all()
        try:
            json_valid = True
            created = False
            try:
                evotor_id = order_json.get("id")
                order = orders.get(evotor_id=evotor_id)
                serializer = OrderSerializer(order, data=order_json)
            except Order.DoesNotExist:
                created = True
                serializer = OrderSerializer(data=order_json)

            if serializer.is_valid():
                order = serializer.save()

                order_creator = OrderCreator()

                for line in order.lines.all():
                    order_creator.update_stock_records(line)

                    event_type = CRMEvent.CREATION if created else CRMEvent.UPDATE
                    CRMEvent.objects.create(
                        body=f"Order created / updated - { order.number }",
                        sender=CRMEvent.PRODUCT,
                        event_type=event_type,
                    )
            else:
                json_valid = False
                logger.error("Ошибка при сериализации %s" % serializer.errors)
                error_msgs.append(f"Ошибка сериализации заказа: {serializer.errors}")

            if not json_valid:
                return ", ".join(error_msgs), False

        except Exception as e:
            logger.error(f"Ошибка при создании / обновлении заказа: {e}", exc_info=True)
            return f"Ошибка при создании / обновлении заказа: {e}", False

        return "Заказ был успешно обновлен", True


class EvotorPushNotifClient(EvotorAPICloud):

    def get_notif(self, application_id, push_id):
        """
        Получить push-уведомление

        Возвращает push-уведомление с указанным идентификатором. Подробнее см. в статье Работа с push-уведомлениями.
        GET /api/apps/{application_id}/push-notifications/{push-id}

        Может передать cursor (Если обектов больше 1000)

        ОТВЕТ:
            {
                "details": [
                    {
                        "active_until": "2018-05-29T16:11:31.079Z",
                        "created_at": "2018-05-29T16:11:31.079Z",
                        "device_id": "string",
                        "rejected_at": "2018-05-29T16:11:31.079Z",
                        "reply": {},
                        "sent_at": "2018-05-29T16:11:31.079Z",
                        "status": "ACCEPTED"
                    }
                ],
                "id": "string",
                "modified_at": "2018-05-29T16:11:31.079Z",
                "status": "ACCEPTED"
            }
        """
        endpoint = f"api/apps/{application_id}/push-notifications/{push_id}"
        return self.send_request(endpoint)

    def send_notif(self, application_id, device_uuid, msg):
        """
        Передать push-уведомление на указанный смарт-терминал

        POST /api/apps/{application_id}/devices/{device_uuid}/push-notifications

        Передаёт push-уведомления на несколько указанных смарт-терминалов. Подробнее см. в статье Работа с push-уведомлениями.

        ТЕЛО:
            {
            "active_until": "2018-05-29T14:17:32.376Z",
            "payload": {}
            }

        ОТВЕТ:
            {
            "details": [
                {
                    "device_id": "20190722-66C8-407E-8024-C3E3B2F3D2B6",
                    "status": "ACCEPTED"
                }
            ],
            "id": "93e892fb-b15d-44c4-bfa2-05168de9c583",
            "modified_at": "2018-05-29T15:44:16.111Z",
            "status": "ACCEPTED"
            }
        """

        # здесь будет преобразование обекта msg и application_id в json
        msg_data = 1

        endpoint = f"api/apps/{application_id}/devices/{device_uuid}/push-notifications"
        return self.send_request(endpoint, "POST", msg_data)

    def send_notifs(self, application_id, msg):
        """
        Передать push-уведомление на несколько смарт-терминалов

        POST /api/apps/{application_id}/push-notifications

        Передаёт push-уведомления на несколько указанных смарт-терминалов. Подробнее см. в статье Работа с push-уведомлениями.

        ТЕЛО:
            {
                "devices": [
                    "string"
                ],
                "active_untill": "2018-05-29T14:17:32.376Z",
                "payload": {}
            }

        ОТВЕТ:
            {
                "details": [
                    {
                        "active_until": "2018-05-29T16:11:31.079Z",
                        "created_at": "2018-05-29T16:11:31.079Z",
                        "device_id": "string",
                        "rejected_at": "2018-05-29T16:11:31.079Z",
                        "reply": {},
                        "sent_at": "2018-05-29T16:11:31.079Z",
                        "status": "ACCEPTED"
                    }
                ],
                "id": "string",
                "modified_at": "2018-05-29T16:11:31.079Z",
                "status": "ACCEPTED"
            }
        """

        # здесь будет преобразование обекта msg и application_id в json
        msg_data = 1

        endpoint = f"api/apps/{application_id}/push-notifications"
        return self.send_request(endpoint, "POST", msg_data)


#  =====


class EvatorCloud(
    EvotorAdditionalClient,
    EvotorDocClient,
    EvotorStaffClient,
    EvotorStoreClient,
    EvotorPushNotifClient,
):
    pass


# ================= запросы к терминалам =================


class EvotorAPIMobileCashier:
    """ "
    Документация для внедрения по ссылке ниже

    ТОКЕН МОБИЛЬНОГО КАССИРА (Для отправки запросов к текрминалам)

    """

    def __init__(
        self,
        base_url: str = "https://mobilecashier.ru/api/",
    ):
        """
        Инициализация клиента для работы с API Эвотор Облако.

        :param api_token: Токен приложения для авторизации в API.
        :param base_url: Базовый URL для API. По умолчанию 'https://api.evotor.ru/api/'. Для запросов к облаку
        :param cashier_url: Базовый URL для API. По умолчанию 'https://api.evotor.ru/api/'. Для запросов к кассе
        """
        self.base_url = base_url

        self.headers = {
            "X-Authorization": f"Bearer {self.get_mobilecashier_token()}",
            "Authorization": f"Bearer {self.get_mobilecashier_token()}",
            "Content-Type": "application/vnd.evotor.v2+json",
            "Accept": "application/vnd.evotor.v2+json",
        }

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
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()  # Проверка на успешный статус запроса (2xx)
            return response.json()  # Возврат данных в формате JSON

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"Other error occurred: {err}")

    def get_mobilecashier_token(self, login: str, password: str):
        pass


class EvotorMobileCashier(EvotorAPIMobileCashier):

    def auth(self, application_id, cashier_id):
        pass
