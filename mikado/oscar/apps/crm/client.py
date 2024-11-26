import json
import requests
import logging
from collections import defaultdict
from django.conf import settings
from django.contrib.auth.models import Group
from django.db.models import F, Q

from rest_framework.renderers import JSONRenderer
from oscar.apps.catalogue.serializers import ProductGroupSerializer, ProductSerializer, ProductsSerializer
from oscar.apps.customer.serializers import UserGroupSerializer, StaffSerializer
from oscar.apps.store.serializers import StoreSerializer, TerminalSerializer
from oscar.core.loading import get_model

logger = logging.getLogger("oscar.crm")

CRMEvent = get_model("crm", "CRMEvent")
Store = get_model("store", "Store")
Terminal = get_model("store", "Terminal")
Staff = get_model("user", "Staff")
GroupEvotor = get_model("auth", "GroupEvotor")
Product = get_model('catalogue', 'Product')
Category = get_model('catalogue', 'Category')

evator_cloud_token = settings.EVOTOR_CLOUD_TOKEN

cashier_login = settings.MOBILE_CASHIER_LOGIN
cashier_pass = settings.MOBILE_CASHIER_PASSWORD

# ================= запросы к облаку =================

class EvotorAPICloud:
    """"
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
            cloud_token: str = evator_cloud_token,   # Токен приложения для авторизации в кассе. Получается у разработчика Эвотор Облако.
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
    

    def send_request(self, endpoint: str, method: str = "GET", data: dict = None, bulk: bool = False):
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
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                logger.error(f"Ошибка HTTP запроса. Неизвестный http метод: {method}")
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()  # Проверка на успешный статус запроса (2xx)
            return response.json()       # Возврат данных в формате JSON
        
        except requests.exceptions.HTTPError as http_err:
            error = ''
            if response.status_code == 400:
                error = 'Неверный запрос Эвотор.'
            if response.status_code == 401:
                error = 'Ошибка авторизации приложения Эвотор.'
            elif response.status_code == 402:
                error = 'Приложение Эвотор не установлено на одно или несколько устройств.'
            elif response.status_code == 403:
                error = 'Нет доступа Эвотор. Ошибка возникает когда у приложения нет разрешения на запрашиваемое действие или пользователь не установил приложение в Личном кабинете.'
            elif response.status_code == 404:
                error = 'Запрашиваемый ресурс не найден в Эвотор.'
            elif response.status_code == 406:
                error = 'Тип содержимого, которое возвращает ресурс не соответствует типу содержимого, которое указанно в заголовке Accept Эвотор.'
            elif response.status_code == 429:
                error = 'Превышено максимальное количество запросов Эвотор в текущем периоде.'
            logger.error(f"Ошибка HTTP запроса при отправке Эвотор запроса: {http_err}")
            return {"error": error}
        except Exception as err:
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
                evotor_id = store_json.get('id')
                evotor_ids.append(evotor_id)
                prt, created = Store.objects.get_or_create(evotor_id=evotor_id)
                serializer = StoreSerializer(prt, data=store_json)
                
                if serializer.is_valid():
                    serializer.save() 
                    event_type = CRMEvent.CREATION if created else CRMEvent.UPDATE
                    CRMEvent.objects.create(
                        body="Store created / or updated",
                        sender=CRMEvent.STORE,
                        type=event_type,
                    )
                else: 
                    json_valid = False
                    logger.error(f"Ошибка сериализации магазина: {serializer.errors}")
                    error_msgs.append(f"Ошибка сериализации магазина: {serializer.errors}")

            if not json_valid:
                return  ', '.join(error_msgs), False
            
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
                evotor_id = terminal_json.get('id')
                evotor_ids.append(evotor_id)
                trm, created = Terminal.objects.get_or_create(evotor_id=evotor_id)
                serializer = TerminalSerializer(trm, data=terminal_json)
                
                if serializer.is_valid():
                    serializer.save() 
                    event_type = CRMEvent.CREATION if created else CRMEvent.UPDATE
                    CRMEvent.objects.create(
                        body="Store created / or updated",
                        sender=CRMEvent.TERMINAL,
                        type=event_type,
                    )
                else: 
                    json_valid = False
                    logger.error(f"Ошибка сериализации терминала: {serializer.errors}")
                    error_msgs.append(f"Ошибка сериализации терминалов: {serializer.errors}")
            
            if not json_valid:
                return  ', '.join(error_msgs), False

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
        staff_json = json.loads(JSONRenderer().render(serializer.data).decode('utf-8'))
        endpoint = "employees"
        
        response = self.send_request(endpoint, "POST", staff_json)
        error = response.get("error", None)
        if not error:
            evotor_id = response.get("id", None)
            staff.evotor_id = evotor_id
            staff.save()

        return staff, error
  

# ========= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (РАБОТА С JSON)

    def create_or_update_site_roles(self, roles_json, is_filtered=False):
        error_msgs = []
        try:
            evotor_ids = []
            json_valid = True
            for role_json in roles_json:
                name = role_json.get('name')
                role, created = Group.objects.get_or_create(name=name)
                serializer = UserGroupSerializer(role, data=role_json)

                evotor_id = role_json.get('id')
                evotor_ids.append((evotor_id, role.id))
                
                if serializer.is_valid():
                    serializer.save() 
                    event_type = CRMEvent.CREATION if created else CRMEvent.UPDATE
                    CRMEvent.objects.create(
                        body="Role role created / or updated",
                        sender=CRMEvent.STAFF,
                        type=event_type,
                    )
                else: 
                    json_valid = False
                    logger.error(f"Ошибка сериализации роли сотрудника: {serializer.errors}")
                    error_msgs.append(f"Ошибка сериализации роли сотрудника: {serializer.errors}")
            
            if not json_valid:
                return  ', '.join(error_msgs), False
            
            if not is_filtered:
                for group_evotor in GroupEvotor.objects.all():
                    if (group_evotor.evotor_id, group_evotor.group_id) not in evotor_ids:
                        group_evotor.delete()

        except Exception as e:
            logger.error(f"Ошибка при обновлении ролей персонала: {e}")
            return f"Ошибка при обновлении ролей персонала: {e}", False

        return "Роли сотрудников были успешно обновлены", True 

    def create_or_update_site_staffs(self, staffs_json, is_filtered=False):
        error_msgs = []
        try:
            evotor_ids = []
            json_valid = True
            created = False
            for staff_json in staffs_json:
                evotor_id = staff_json.get('id')
                evotor_ids.append(evotor_id)
                try:
                    staff = Staff.objects.get(evotor_id=evotor_id)
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
                        type=event_type,
                    )
                else: 
                    json_valid = False
                    logger.error(f"Ошибка сериализации сотрудника: {serializer.errors}")
                    error_msgs.append(f"Ошибка сериализации сотрудника: {serializer.errors}")
            
            if not json_valid:
                return  ', '.join(error_msgs), False

            if not is_filtered:
                for staff in Staff.objects.all():
                    if staff.evotor_id not in evotor_ids:
                        staff.evotor_id = None
                        staff.save()

        except Exception as e:
            logger.error(f"Ошибка при обновлении списка сотрудников: {e}")
            return f"Ошибка при обновлении списка сотрудников: {e}", False

        return "Сотрудники были успешно обновлены", True 
 

class EvotorProductClient(EvotorAPICloud):
    """" 
    Работа с вариативными товарами
    https://developer.evotor.ru/docs/rest_product_modifications_guide.html 
    """

# ========= ПОЛУЧЕНИЕ ДАННЫХ

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
    
    def get_product_by_id(self, store_id, product_id):
        """
        Получить товар

        Возвращает из магазина товар или модификацию товара с указанным идентификатором.
        GET /stores/{store-id}/products/{product-id}

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
                "type": "NORMAL",
                "id": "01ba18b6-8707-5f47-3d9c-4db058054cb2",
                "quantity": 12,
                "cost_price": 100.123,
                "attributes_choices": {},
                "store_id": "20180820-7052-4047-807D-E82C50000000",
                "user_id": "00-000000000000000",
                "created_at": "2018-09-11T16:18:35.397+0000",
                "updated_at": "2018-09-11T16:18:35.397+0000"
            }
        """
        endpoint = f"stores/{store_id}/products/{product_id}"
        return self.send_request(endpoint)
    
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
    
# ========= ОТПРАВКА ДАННЫХ

    # products ============

    # ===  не вызываются напрямую 

    def create_evotor_products(self, products, store_id):
        """
        Создать товар

        Создает новый товар или модификацию товара в магазине. Идентификаторы объектов формирует Облако.
        POST /stores/{store-id}/products

        Чтобы передать несколько объектов дополните заголовок Content-Type модификатором +bulk.

        products - список объектов Product

        ТЕЛО: 
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
            "is_age_limited": true,
            "barcodes": [
                "2000000000060"
            ],
            "type": "ALCOHOL_NOT_MARKED"
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
                "is_age_limited": true,
                "barcodes": [
                    "2000000000060"
                ],
                "type": "ALCOHOL_NOT_MARKED",
                "id": "01ba18b6-8707-5f47-3d9c-4db058054cb2",
                "quantity": 12,
                "cost_price": 100.123,
                "attributes_choices": {},
                "store_id": "20180820-7052-4047-807D-E82C50000000",
                "user_id": "00-000000000000000",
                "created_at": "2018-09-11T16:18:35.397+0000",
                "updated_at": "2018-09-11T16:18:35.397+0000"
            }
        """
        if len(products) > 1:
            bulk = True
            serializer = ProductsSerializer({"items": products}, context={"store_id": store_id})
            products_json = json.loads(JSONRenderer().render(serializer.data.get('items')).decode('utf-8'))
        else:
            bulk = False
            serializer = ProductSerializer(products[0], context={"store_id": store_id})
            products_json = json.loads(JSONRenderer().render(serializer.data).decode('utf-8'))

        endpoint = f"stores/{store_id}/products"
        response = self.send_request(endpoint, "POST", products_json, bulk)
        error = response.get("error", None) if isinstance(response, dict) else None
    
        if not error:
            if bulk:
                for product_response in response:
                    name = product_response.get("name")
                    product = next((p for p in products if p.title == name), None)
                    if product:
                        product.evotor_id = product_response.get("id")
                        product.save()
            else:
                products[0].evotor_id = response.get("id")
                products[0].save()

        return products, error
    
    def update_evotor_products(self, products, store_id):
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
        serializer = ProductsSerializer({"items": products}, context={"store_id": store_id})
        products_json = json.loads(JSONRenderer().render(serializer.data.get('items')).decode('utf-8'))

        endpoint = f"stores/{store_id}/products"
        response = self.send_request(endpoint, "PUT", products_json, True)
        error = response.get("error", None) if isinstance(response, dict) else None
    
        return products, error
    
    # === вызываются напрямую

    def update_or_create_evotor_product(self, product):
        """
        Создать/заменить товар

        Создаёт или заменяет в магазине один товар или модификацию товара с указанным идентификатором.
        PUT /stores/{store-id}/products/{product-id}

        Чтобы передать несколько объектов дополните заголовок Content-Type модификатором +bulk.

        products - список объектов Product

        ТЕЛО: 
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
            "is_age_limited": true,
            "barcodes": [
                "2000000000060"
            ],
            "type": "ALCOHOL_NOT_MARKED"
        }

        ОТВЕТ: 
            {
                "id": "ca187ddc-8d1b-4d0e-b20d-c509082da528",
                "modified_at": "2018-01-01T00:00:00.000Z",
                "status": "COMPLETED",
                "type": "product",
                "details": [
                    { }
                ]
            }
        """
        return self.update_or_create_evotor_products([product])

    def update_or_create_evotor_products(self, products):
        """
        Создаёт или заменяет товары или модификации товаров в магазине. Идентификаторы объектов формирует клиент API.

        Создает новый товар или модификацию товара в магазине. Идентификаторы объектов формирует Облако.
        PUT /stores/{store-id}/products

        Чтобы передать несколько объектов дополните заголовок Content-Type модификатором +bulk.

        products - список объектов Product

        ТЕЛО: 
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
            "is_age_limited": true,
            "barcodes": [
                "2000000000060"
            ],
            "type": "ALCOHOL_NOT_MARKED"
        }

        ОТВЕТ: 
            {
                "id": "ca187ddc-8d1b-4d0e-b20d-c509082da528",
                "modified_at": "2018-01-01T00:00:00.000Z",
                "status": "COMPLETED",
                "type": "product",
                "details": [
                    { }
                ]
            }
        """
        errors = []
        grouped_products = {"create": defaultdict(list), "update": defaultdict(list)}

        for product in products:
            key = "update" if product.evotor_id else "create"
            for stockrecord in product.stockrecords.all():
                evotor_id = stockrecord.store.evotor_id
                grouped_products[key][evotor_id].append(product)

        for action, products_by_store in grouped_products.items():
            for store_id, grouped_products in products_by_store.items():
                if action == "create":
                    prds, err = self.create_evotor_products(grouped_products, store_id)
                else:
                    prds, err = self.update_evotor_products(grouped_products, store_id)
                if err:
                    errors.append(err)

        return products, ", ".join(errors)

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

        for stockrecord in product.stockrecords.all():
            store_id = stockrecord.store.evotor_id
            product_id = product.evotor_id

            if store_id and product_id:
                stockrecord_json = {
                    "quantity": stockrecord.num_in_stock or 0,
                    "cost_price": float(stockrecord.cost_price) or 0,
                    "price": float(stockrecord.price) or 0,
                }
                endpoint = f"stores/{store_id}/products/{product_id}"
                response = self.send_request(endpoint, "PATCH", stockrecord_json)

                if isinstance(response, dict) and "error" in response:
                    errors.append(response["error"])

        return product, ", ".join(errors)
    
    def delete_evotor_product(self, product):
        """
        Удалить товар или модификацию товара

        Удаляет из магазина товар или модификацию товара с указанным идентификатором.
        DELETE /stores/{store-id}/products/{product-id}

        product_id - строка ID Products

        """
        errors = []

        for stockrecord in product.stockrecords.all():
            store_id = stockrecord.store.evotor_id
            product_id = product.evotor_id

            if store_id and product_id:
                endpoint = f"stores/{store_id}/products/{product_id}"
                response = self.send_request(endpoint, "DELETE")

                if isinstance(response, dict) and "error" in response:
                    errors.append(response["error"])

        return product, ", ".join(errors)


    # def delete_evotor_products(self, store_id, products_id):
    #     """
    #     Удалить несколько товаров или модификаций товаров данные товара
    #     DELETE /stores/{store-id}/products

    #     Удаляет товары и модификации товаров из магазина.
    #     Чтобы удалить несколько товаров, в параметре id, укажите через запятую идентификаторы товаров к удалению.
    #     В рамках одного запроса можно удалить до 100 товаров.

    #     products_id - список ID Products

    #     """
    #     bulk = False

    #     if len(products_id) > 1:
    #         bulk = True

    #     # здесть будет преобразование обекта списка в json
    #     products_data = json.dump(products_id)

    #     endpoint = f"stores/{store_id}/products"
    #     return self.send_request(endpoint, "DELETE", products_data, bulk)

    # groups ============

    def create_evotor_groups(self, products, store_id):
        """
        Создать товар

        Создает новый товар или модификацию товара в магазине. Идентификаторы объектов формирует Облако.
        POST /stores/{store-id}/products

        Чтобы передать несколько объектов дополните заголовок Content-Type модификатором +bulk.

        products - список объектов Product

        ТЕЛО: 
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
            "is_age_limited": true,
            "barcodes": [
                "2000000000060"
            ],
            "type": "ALCOHOL_NOT_MARKED"
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
                "is_age_limited": true,
                "barcodes": [
                    "2000000000060"
                ],
                "type": "ALCOHOL_NOT_MARKED",
                "id": "01ba18b6-8707-5f47-3d9c-4db058054cb2",
                "quantity": 12,
                "cost_price": 100.123,
                "attributes_choices": {},
                "store_id": "20180820-7052-4047-807D-E82C50000000",
                "user_id": "00-000000000000000",
                "created_at": "2018-09-11T16:18:35.397+0000",
                "updated_at": "2018-09-11T16:18:35.397+0000"
            }
        """
        bulk = False

        # здесть будет преобразование обекта Product в json
        serializer = ProductsSerializer(products)
        products_json = json.loads(JSONRenderer().render(serializer.data).decode('utf-8'))
        if len(products) > 1:
            bulk = True
            
        endpoint = f"stores/{store_id}/products"
        response = self.send_request(endpoint, "POST", products_json, bulk)
        error = response.get("error", None)
    
        if not error:
            for product_response in response:
                name = product_response.get("name")
                product = products.filter(title=name)
                if product:
                    product.evotor_id = product_response.get("id")
                    product.save()
                    
        return products, error
    
    def update_evotor_groups(self, products, store_id):
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
        bulk = False

        # здесть будет преобразование обекта Product в json
        serializer = ProductsSerializer(products)
        products_json = json.loads(JSONRenderer().render(serializer.data).decode('utf-8'))
        if len(products) > 1:
            bulk = True
            
        endpoint = f"stores/{store_id}/products"
        response = self.send_request(endpoint, "PUT", products_json, bulk)
        error = response.get("error", None)
    
        return products, error
    
    def update_or_create_evotor_group(self, product, store_id):
        """
        Создать/заменить товар

        Создаёт или заменяет в магазине один товар или модификацию товара с указанным идентификатором.
        PUT /stores/{store-id}/products/{product-id}

        Чтобы передать несколько объектов дополните заголовок Content-Type модификатором +bulk.

        products - список объектов Product

        ТЕЛО: 
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
            "is_age_limited": true,
            "barcodes": [
                "2000000000060"
            ],
            "type": "ALCOHOL_NOT_MARKED"
        }

        ОТВЕТ: 
            {
                "id": "ca187ddc-8d1b-4d0e-b20d-c509082da528",
                "modified_at": "2018-01-01T00:00:00.000Z",
                "status": "COMPLETED",
                "type": "product",
                "details": [
                    { }
                ]
            }
        """

        if product.evotor_id:
            return self.update_evotor_products([product], store_id, product.evotor_id)
        
        return self.create_evotor_products([product], store_id)

    def update_or_create_evotor_groups(self, products, store_id):
        """
        Создаёт или заменяет товары или модификации товаров в магазине. Идентификаторы объектов формирует клиент API.

        Создает новый товар или модификацию товара в магазине. Идентификаторы объектов формирует Облако.
        PUT /stores/{store-id}/products

        Чтобы передать несколько объектов дополните заголовок Content-Type модификатором +bulk.

        products - список объектов Product

        ТЕЛО: 
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
            "is_age_limited": true,
            "barcodes": [
                "2000000000060"
            ],
            "type": "ALCOHOL_NOT_MARKED"
        }

        ОТВЕТ: 
            {
                "id": "ca187ddc-8d1b-4d0e-b20d-c509082da528",
                "modified_at": "2018-01-01T00:00:00.000Z",
                "status": "COMPLETED",
                "type": "product",
                "details": [
                    { }
                ]
            }
        """

        products_to_create = products.filter(evotor_id__isnull=True)
        products_to_update = products.filter(evotor_id__isnull=False)

        prds_crt, err_crt = self.create_evotor_products(products_to_create, store_id)
        prds_upd, err_upd = self.update_evotor_products(products_to_update, store_id)

        return {
            "created": (prds_crt, err_crt),
            "updated": (prds_upd, err_upd),
        }

    def delete_evotor_group(self, store_id, product_id):
        """
        Удалить товар или модификацию товара

        Удаляет из магазина товар или модификацию товара с указанным идентификатором.
        DELETE /stores/{store-id}/products/{product-id}

        product_id - строка ID Products

        """
        # здесть будет преобразование обекта списка в json
        products_data = json.dump(product_id)

        endpoint = f"stores/{store_id}/products/{product_id}"
        return self.send_request(endpoint, "DELETE", products_data)

    def delete_evotor_groups(self, store_id, products_id):
        """
        Удалить несколько товаров или модификаций товаров данные товара
        DELETE /stores/{store-id}/products

        Удаляет товары и модификации товаров из магазина.
        Чтобы удалить несколько товаров, в параметре id, укажите через запятую идентификаторы товаров к удалению.
        В рамках одного запроса можно удалить до 100 товаров.

        products_id - список ID Products

        """
        bulk = False

        if len(products_id) > 1:
            bulk = True

        # здесть будет преобразование обекта списка в json
        products_data = json.dump(products_id)

        endpoint = f"stores/{store_id}/products"
        return self.send_request(endpoint, "DELETE", products_data, bulk)

# ========= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (РАБОТА С JSON)

    def create_or_update_site_products(self, products_json, is_filtered=False):
        error_msgs = []
        try:
            evotor_ids = []
            json_valid = True
            created = False
            for product_json in products_json:
                evotor_id = product_json.get('id')
                evotor_ids.append(evotor_id)
                try:
                    prd = Product.objects.get(evotor_id=evotor_id)
                    serializer = ProductSerializer(prd, data=product_json)
                except Product.DoesNotExist:
                    created = True
                    serializer = ProductSerializer(data=product_json)
                
                if serializer.is_valid():
                    product = serializer.save() 
                    event_type = CRMEvent.CREATION if created else CRMEvent.UPDATE
                    CRMEvent.objects.create(
                        body=f"Product created / updated - { product.title }",
                        sender=CRMEvent.PRODUCT,
                        type=event_type,
                    )
                else: 
                    json_valid = False
                    logger.error(f"Ошибка сериализации товара: {serializer.errors}")
                    error_msgs.append(f"Ошибка сериализации товара: {serializer.errors}")

            if not json_valid:
                return  ', '.join(error_msgs), False
            
            if not is_filtered:
                for product in Product.objects.all():
                    if product.evotor_id not in evotor_ids:
                        product.evotor_id = None
                        product.save()

        except Exception as e:
            logger.error(f"Ошибка при обновлении товара: {e}", exc_info=True)
            return f"Ошибка при обновлении товара: {e}", False

        return "Магазины были успешно обновлены", True 

    def create_or_update_site_groups(self, groups_json, is_filtered=False):
        error_msgs = []
        try:
            evotor_ids = []
            json_valid = True
            for group_json in groups_json:
                evotor_id = group_json.get('id')
                evotor_ids.append(evotor_id)
                trm, created = Terminal.objects.get_or_create(evotor_id=evotor_id)
                serializer = ProductGroupSerializer(trm, data=group_json)
                
                if serializer.is_valid():
                    serializer.save() 
                    event_type = CRMEvent.CREATION if created else CRMEvent.UPDATE
                    CRMEvent.objects.create(
                        body="Store created / or updated",
                        sender=CRMEvent.TERMINAL,
                        type=event_type,
                    )
                else: 
                    json_valid = False
                    logger.error(f"Ошибка сериализации терминала: {serializer.errors}")
                    error_msgs.append(f"Ошибка сериализации терминалов: {serializer.errors}")
            
            if not json_valid:
                return  ', '.join(error_msgs), False

            if not is_filtered:
                for terminal in Terminal.objects.all():
                    if terminal.evotor_id not in evotor_ids:
                        terminal.delete()

        except Exception as e:
            logger.error(f"Ошибка при обновлении терминалов: {e}", exc_info=True)            
            return f"Ошибка при обновлении терминалов: {e}", False

        return "Терминалы были успешно обновлены", True 



class EvotorDocClient(EvotorAPICloud):

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
 

class EvatorCloud(EvotorProductClient, EvotorDocClient, EvotorStaffClient, EvotorStoreClient, EvotorPushNotifClient):
    pass


# ================= запросы к терминалам =================


class EvotorAPIMobileCashier:
    """"
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
    

    def send_request(self, endpoint: str, method: str = "GET", data: dict = None, bulk: bool = False):
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
            return response.json()       # Возврат данных в формате JSON

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"Other error occurred: {err}")


    def get_mobilecashier_token(self, login: str, password: str):
        pass


class EvotorMobileCashier(EvotorAPIMobileCashier):

    def auth(self, application_id, cashier_id):
        pass

