# import logging

# from django.conf import settings
# from decimal import Decimal as D
# from django.urls import reverse_lazy
# from requests.exceptions import HTTPError
# from komtet_kassa_sdk.v2 import (
#     Check, CorrectionCheck, Client, Intent, TaxSystem, VatRate, CorrectionType, PaymentMethod,
#     Agent, AgentType, PaymentType, PaymentObject, MarkTypes, MeasureTypes, Position
# )

# logger = logging.getLogger("oscar.order")
# callback_url = reverse_lazy('order:callback')

# shop_id = ""
# secret_key = ""

# tax_system = settings.TAX_SYSTEM
# payment_address = settings.ALLOWED_HOSTS[0]
# payment_method = PaymentMethod.PRE_PAYMENT_FULL


# class EvotorKomtet:

#     unit_codes = {
#         "шт": MeasureTypes.PIECE,
#         "г": MeasureTypes.GRAMM,
#         "кг": MeasureTypes.KILOGRAMM,
#         "т": MeasureTypes.TON,
#         "см": MeasureTypes.CENTIMETER,
#         "дм": MeasureTypes.DECIMETER,
#         "м": MeasureTypes.METER,
#         "см²": MeasureTypes.SQUARE_CENTIMETER,
#         "дм²": MeasureTypes.SQUARE_DECIMETER,
#         "м²": MeasureTypes.SQUARE_METER,
#         "мл": MeasureTypes.MILLILITER,
#         "л": MeasureTypes.LITER,
#         "м³": MeasureTypes.CUBIC_METER,
#         "кВт·ч": MeasureTypes.KILOWATT_HOUR,
#         "Гкал": MeasureTypes.KILOWATT_HOUR,
#         "день": MeasureTypes.DAY,
#         "час": MeasureTypes.HOUR,
#         "минута": MeasureTypes.MINUTE,
#         "секунда": MeasureTypes.SECOND,
#         "КБ": MeasureTypes.KILOBYTE,
#         "МБ": MeasureTypes.MEGABYTE,
#         "ГБ": MeasureTypes.GIGABYTE,
#         "ТБ": MeasureTypes.TERABYTE,
#     }

#     vats = {
#         "none":VatRate.RATE_NO,
#         "vat0":VatRate.RATE_0,
#         "vat10":VatRate.RATE_10,
#         "vat110":VatRate.RATE_110,
#         "vat20":VatRate.RATE_20,
#         "vat120":VatRate.RATE_120,
#     }

#     # Receipt

#     def create_check(self, order_json):
#         client = Client(shop_id, secret_key)

#         lines = order_json.get('lines')
#         user = order_json.get('user')

#         check = Check(order_json.get('number'), Intent.SELL)
#         check.set_client(email=user.get('email'), phone=user.get('username'))
#         check.set_company(payment_address=payment_address, tax_system=tax_system)

#         for line in lines:
#             check.add_position(
#                 Position(
#                     id=line.get('evotor_id'),
#                     name=line.get('name'),
#                     price=line.get('unit_price'), # Цена за единицу
#                     quantity=line.get('quantity'),  # Количество единиц
#                     total=line.get('line_price'), # Общая стоимость позиции
#                     measure=self.unit_codes.get(line.get('measure_name'), MeasureTypes.PIECE), # Единица измерения
#                     payment_method=payment_method, # Метод расчёта
#                     vat=self.unit_codes.get(line.get('vat'), VatRate.RATE_NO),  # Тип налога
#                     payment_object=PaymentObject.PRODUCT # Объект расчёта
#                 )
#             )

#         sipping_price = D(order_json.get('shipping'))
#         if sipping_price > 0:
#             check.add_position(
#                 Position(
#                     name="Доставка",
#                     price=sipping_price, # Цена за единицу
#                     quantity=1,  # Количество единиц
#                     total=sipping_price, # Общая стоимость позиции
#                     measure=MeasureTypes.OTHER_MEASURMENTS, # Единица измерения
#                     payment_method=payment_method, # Метод расчёта
#                     vat=VatRate.RATE_20, #переделай, Тип налога
#                     payment_object=PaymentObject.SERVICE # Объект расчёта
#                 )
#             )

#         check.add_payment(order_json.get('amount_allocated'))
#         check.set_print(False)
#         check.set_callback_url(f"https://{payment_address}{callback_url}")

#         try:
#             client.create_task(check)
#         except HTTPError as exc:
#             logger.error(f"Ошибка при отправке заказа в очередь КОМТЕТ: {exc.response.text}")

#     def refund_check(self, order_json):
#         pass

#     # Order Evotor

#     def create_order(self, order_json):
#         lines = order_json.get('lines')
#         user = order_json.get('user')

#         check = Check(order_json.get('number'), Intent.SELL)
#         check.set_client(email=user.get('email'), phone=user.get('username'))
#         check.set_company(payment_address=payment_address, tax_system=tax_system)

#         for line in lines:
#             check.add_position(
#                 Position(
#                     id=line.get('evotor_id'),
#                     name=line.get('name'),
#                     price=line.get('unit_price'), # Цена за единицу
#                     quantity=line.get('quantity'),  # Количество единиц
#                     total=line.get('line_price'), # Общая стоимость позиции
#                     measure=self.unit_codes.get(line.get('measure_name'), MeasureTypes.PIECE), # Единица измерения
#                     payment_method=payment_method, # Метод расчёта
#                     vat=self.unit_codes.get(line.get('vat'), VatRate.RATE_NO),  # Тип налога
#                     payment_object=PaymentObject.PRODUCT # Объект расчёта
#                 )
#             )

#         sipping_price = D(order_json.get('shipping'))
#         if sipping_price > 0:
#             check.add_position(
#                 Position(name="Доставка",
#                     price=sipping_price, # Цена за единицу
#                     quantity=1,  # Количество единиц
#                     total=sipping_price, # Общая стоимость позиции
#                     measure=MeasureTypes.OTHER_MEASURMENTS, # Единица измерения
#                     payment_method=payment_method, # Метод расчёта
#                     vat=VatRate.RATE_20, #переделай, Тип налога
#                     payment_object=PaymentObject.SERVICE # Объект расчёта
#                 )
#             )

#         check.add_payment(order_json.get('amount_allocated'))
#         check.set_print(False)
#         check.set_callback_url(f"https://{payment_address}{callback_url}")

#         try:
#             client.create_task(check)
#         except HTTPError as exc:
#             logger.error(f"Ошибка при отправке заказа: {exc.response.text}")

#     def update_order(self, order_json):
#         pass

#     def delete_order(self, order_json):
#         pass

#     def order_info(self, order_json):
#         pass

#     # Employees

#     def get_employees(self, order_json):
#         pass

#     def create_employee(self, order_json):
#         pass

#     def update_employee(self, order_json):
#         pass

#     def delete_employee(self, order_json):
#         pass


#     # position_name = 'Наименование позиции'
#     # position_price = 100  # Цена позиции

#     # # Единицы измерений
#     # measure = MeasureTypes.PIECE
#     # # measure = MeasureTypes.PIECE
#     # # measure = MeasureTypes.GRAMM
#     # # measure = MeasureTypes.KILOGRAMM
#     # # measure = MeasureTypes.TON
#     # # measure = MeasureTypes.CENTIMETER
#     # # measure = MeasureTypes.DECIMETER
#     # # measure = MeasureTypes.METER
#     # # measure = MeasureTypes.SQUARE_CENTIMETER
#     # # measure = MeasureTypes.SQUARE_DECIMETER
#     # # measure = MeasureTypes.SQUARE_METER
#     # # measure = MeasureTypes.MILLILITER
#     # # measure = MeasureTypes.LITER
#     # # measure = MeasureTypes.CUBIC_METER
#     # # measure = MeasureTypes.KILOWATT_HOUR
#     # # measure = MeasureTypes.GIGA_CALORIE
#     # # measure = MeasureTypes.DAY
#     # # measure = MeasureTypes.HOUR
#     # # measure = MeasureTypes.MINUTE
#     # # measure = MeasureTypes.SECOND
#     # # measure = MeasureTypes.KILOBYTE
#     # # measure = MeasureTypes.MEGABYTE
#     # # measure = MeasureTypes.GIGABYTE
#     # # measure = MeasureTypes.TERABYTE
#     # # measure = MeasureTypes.OTHER_MEASURMENTS

#     # # Налоговая ставка
#     # vat_rate = VatRate.RATE_NO  # Без НДС
#     # # vat_rate = VatRate.RATE_0  # НДС 0%
#     # # vat_rate = VatRate.RATE_5  # НДС 5%
#     # # vat_rate = VatRate.RATE_7  # НДС 7%
#     # # vat_rate = VatRate.RATE_10  # НДС 10%
#     # # vat_rate = VatRate.RATE_20  # НДС 20%
#     # # vat_rate = VatRate.RATE_105  # НДС 5/105
#     # # vat_rate = VatRate.RATE_107  # НДС 7/107
#     # # vat_rate = VatRate.RATE_110  # НДС 10/110
#     # # vat_rate = VatRate.RATE_120  # НДС 20/120

#     # #Способ расчёта
#     # payment_method = PaymentMethod.PRE_PAYMENT_FULL
#     # # payment_method = PaymentMethod.PRE_PAYMENT_PART
#     # # payment_method = PaymentMethod.FULL_PAYMENT
#     # # payment_method = PaymentMethod.ADVANCE
#     # # payment_method = PaymentMethod.CREDIT_PART
#     # # payment_method = PaymentMethod.CREDIT_PAY
#     # # payment_method = PaymentMethod.CREDIT


#     # # Признак рассчета
#     # payment_object = PaymentObject.PRODUCT
#     # # payment_object = PaymentObject.PRODUCT_PRACTICAL
#     # # payment_object = PaymentObject.WORK
#     # # payment_object = PaymentObject.SERVICE
#     # # payment_object = PaymentObject.GAMBLING_BET
#     # # payment_object = PaymentObject.GAMBLING_WIN
#     # # payment_object = PaymentObject.LOTTERY_BET
#     # # payment_object = PaymentObject.LOTTERY_WIN
#     # # payment_object = PaymentObject.RID
#     # # payment_object = PaymentObject.PAYMENT
#     # # payment_object = PaymentObject.COMMISSION
#     # # payment_object = PaymentObject.COMPOSITE
#     # # payment_object = PaymentObject.PAY
#     # # payment_object = PaymentObject.OTHER
#     # # payment_object = PaymentObject.PROPERTY_RIGHT
#     # # payment_object = PaymentObject.NON_OPERATING
#     # # payment_object = PaymentObject.INSURANCE
#     # # payment_object = PaymentObject.SALES_TAX
#     # # payment_object = PaymentObject.RESORT_FEE
#     # # payment_object = PaymentObject.DEPOSIT
#     # # payment_object = PaymentObject.CONSUMPTION
#     # # payment_object = PaymentObject.SOLE_PROPRIETOR_CPI_CONTRIBUTINS
#     # # payment_object = PaymentObject.CPI_CONTRIBUTINS
#     # # payment_object = PaymentObject.SOLE_PROPRIETOR_CMI_CONTRIBUTINS
#     # # payment_object = PaymentObject.CMI_CONTRIBUTINS
#     # # payment_object = PaymentObject.CSI_CONTRIBUTINS
#     # # payment_object = PaymentObject.CASINO_PAYMENT
#     # # payment_object = PaymentObject.PAYMENT_OF_THE_MONEY
#     # # payment_object = PaymentObject.ATHM
#     # # payment_object = PaymentObject.ATM
#     # # payment_object = PaymentObject.THM
#     # # payment_object = PaymentObject.TM

#     # # Создание позиции
#     # position = Position(id=1,  # Идентификатор позиции в магазине
#     #                     name='Наименование позиции',
#     #                     price=10, # Цена за единицу
#     #                     quantity=1,  # Количество единиц
#     #                     total=10, # Общая стоимость позиции
#     #                     excise=10, # Акциз
#     #                     measure=measure, # Единица измерения
#     #                     user_data='Дополнительный реквизит предмета расчета',
#     #                     payment_method=payment_method, # Метод расчёта
#     #                     vat=vat_rate,  # Тип налога
#     #                     payment_object=payment_object # Объект расчёта
#     # )


#     # # Типы маркировок
#     # mark_type = MarkTypes.EAN13
#     # # mark_type = MarkTypes.UNKNOWN
#     # # mark_type = MarkTypes.EAN8
#     # # mark_type = MarkTypes.ITF14
#     # # mark_type = MarkTypes.GS10
#     # # mark_type = MarkTypes.GS1M
#     # # mark_type = MarkTypes.GS10
#     # # mark_type = MarkTypes.SHORT
#     # # mark_type = MarkTypes.FUR
#     # # mark_type = MarkTypes.EGAIS20
#     # # mark_type = MarkTypes.EGAIS30

#     # # Добавление кода маркировки в позицию
#     # position.set_mark_code(type=mark_type, code='1234567890123')

#     # # Установка дробности маркированного товара
#     # position.set_mark_quantity(numerator=1, denominator=2)

#     # # Если нужна информация о агенте

#     # # Создание агента
#     # agent_info = Agent(agent_type=AgentType.AGENT, phone='+79998887766',
#     #                     name='Названиепоставщика', inn='287381373424')

#     # # Если нужно, установка платёжного агента
#     # agent_info.set_paying_agent(operation='Операция1', phones=['+79998887766'])

#     # # Если нужно, установка оператора приёма платежей
#     # agent_info.set_receive_payments_operator(phones=['+79998887766'])

#     # # Если нужно, установка оператора перевода средств
#     # agent_info.set_money_transfer_operator(phones=['+79998887766'], name='Операторперевода',
#     #                                         address='г. Москва, ул. Складочная д.3',
#     #                                         inn='8634330204')

#     # # Добавление агента в позицию
#     # position.set_agent(agent_info)

#     # # Добавление позиции
#     # check.add_position(position)

#     # # Добавление суммы расчёта
#     # check.add_payment(300)

#     # # Если нужно распечатать чек (по умолчанию False)
#     # check.set_print(True)

#     # # Если нужно задать данные по кассиру, по умолчанию возьмутся с ФН
#     # check.set_cashier('Иваров И.П.', '1234567890123')

#     # # Если нужно установить дополнительные параметры чека
#     # check.set_additional_check_props('445334544')

#     # # Если нужно получитиь отчёт об успешной фискализации
#     # check.set_callback_url('http://shop.pro/fiscal_check/callback')

#     # # Отправка запроса
#     # try:
#     #     task = client.create_task(check, 'идентификатор очереди')
#     # except HTTPError as exc:
#     #     print(exc.response.text)
#     # else:
#     #     print(task)
#     # # Task(id=1, external_id=2, print_queue_id=3, state='new')
#     # # id - идентификатор задачи
#     # # external_id - идентификатор операции в магазине
#     # # print_queue_id - идентификатор очереди
#     # # state - состояние задачи


#     # # Создание чека коррекции

#     # intent = Intent.SELL_CORRECTION  # Коррекция прихода
#     # # intent = Intent.BUY_CORRECTION # Коррекция расхода
#     # # intent = Intent.SELL_RETURN_CORRECTION # Коррекция возврата прихода
#     # # intent = Intent.BUY_RETURN_CORRECTION # Коррекция возврата расхода

#     # check = CorrectionCheck(oid, intent)

#     # # Установка данных компании
#     # check.set_company(payment_address=payment_address, tax_system=tax_system)

#     # payment_type = PaymentType.CARD # Тип оплаты, корректирующей суммы
#     # # payment_method = PaymentType.CARD # электронные
#     # # payment_method = PaymentType.CASH # наличные

#     # # Установка суммы коррекции
#     # check.add_payment(12, payment_type)

#     # correction_type = CorrectionType.SELF # Тип коррекции
#     # # correction_type = CorrectionType.SELF # Самостоятельно
#     # # correction_type = CorrectionType.FORCED # По предписанию

#     # # Установка данных коррекции
#     # check.set_correction_info(correction_type,
#     #                         '31.03.2022', # Дата документа коррекции в формате 'dd.mm.yyyy'
#     #                         'K11',        # Номер документа коррекции
#     # )

#     # # Создаём позицию коррекции
#     # position = Position(name='Товар', price=10, quantity=5, total=50,
#     #                     measure=measure, payment_method=payment_method,
#     #                     payment_object=payment_object, vat=vat_rate)

#     # # Добавляем позицию коррекции
#     # check.add_position(position)

#     # # Указание уполномоченного лица
#     # check.set_authorised_person(
#     #     name='Иванов И.И',
#     #     inn='123456789012'
#     # )

#     # # Если нужно получитиь отчёт об успешной фискализации
#     # check.set_callback_url('http://shop.pro/fiscal_check/callback')

#     # # Отправка запроса
#     # try:
#     #     task = client.create_task(check, 'идентификатор очереди')
#     # except HTTPError as exc:
#     #     print(exc.response.text)
#     # else:
#     #     print(task)
#     # # Task(id=1, external_id=2, print_queue_id=3, state='new')
#     # # id - идентификатор задачи
#     # # external_id - идентификатор операции в магазине
#     # # print_queue_id - идентификатор очереди
#     # # state - состояние задачи

#     # # Получение информации о поставленной на фискализацию задаче:
#     # try:
#     #     task_info = client.get_task_info('идентификатор задачи')
#     # except HTTPError as exc:
#     #     print(exc.response.text)
#     # else:
#     #     print(task_info)
#     # # TaskInfo(id=234, external_id='4321', state='done', error_description=None,
#     # #          fiscal_data={'i': '111',
#     # #                       'fn': '2222222222222222',
#     # #                       't': '3333333333333',
#     # #                       'n': 4,
#     # #                       'fp': '555555555',
#     # #                       's': '6666.77'})
#     # # id - идентификатор задачи
#     # # external_id - идентификатор операции в магазине
#     # # state - состояние задачи
#     # # error_description - описание возникшей ошибки, когда state=='error'
#     # # fiscal_data - фискальные данные


#     # # Чтобы проверить, является ли очередь активной, выполните:
#     # client.is_queue_active('идентификатор очереди')

#     # # Вы можете указать идентификатор очереди по умолчанию с помощью:
#     # client.set_default_queue('идентификатор очереди по умолчанию')
#     # # В этом случае можно не указывать идентификатор очереди всякий раз,
#     # # когда нужно распечатать чек или проверить состояние очереди:
#     # assert client.is_queue_active() is True
#     # try:
#     #     task = client.create_task(check)
#     # except HTTPError as exc:
#     #     print(exc.response.text)
#     # else:
#     #     print(task)


# # ========== Сериализоторы АТОЛ для отправки / изменения чеков ==========


# # class ReceiptLineSerializer(serializers.Serializer):

# #     unit_codes = {
# #         "шт": 0,
# #         "г": 10,
# #         "кг": 11,
# #         "т": 12,
# #         "см": 20,
# #         "дм": 21,
# #         "м": 22,
# #         "см²": 30,
# #         "дм²": 31,
# #         "м²": 32,
# #         "мл": 40,
# #         "л": 41,
# #         "м³": 42,
# #         "кВт·ч": 50,
# #         "Гкал": 51,
# #         "сутки": 70,
# #         "день": 70,
# #         "час": 71,
# #         "минута": 72,
# #         "секунда": 73,
# #         "КБ": 80,
# #         "МБ": 81,
# #         "ГБ": 82,
# #         "ТБ": 83,
# #     }

# #     vats = {
# #         "none":"NO_VAT",
# #         "vat0":"VAT_0",
# #         "vat10":"VAT_10",
# #         "vat110":"VAT_10_110",
# #         "vat20":"VAT_18",
# #         "vat120":"VAT_18_118",
# #     }

# #     def to_representation(self, instance):
# #         return {
# #             "name": instance.get_full_name(),
# #             "price": instance.unit_price,
# #             "quantity": instance.quantity,
# #             "measure": self.unit_codes.get(instance.product.get_product_class().measure_name, 255),
# #             "sum": instance.line_price,
# #             "payment_method": "full_payment",
# #             "payment_object": 1,
# #             "vat": {"type": self.vats.get(instance.tax_code, "vat20")},
# #         }


# # class ReceiptSerializer(serializers.Serializer):
# #      def to_representation(self, instance):
# #         representation = {
# #             "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
# #             "external_id": instance.id,
# #             "service": {"callback_url": f"https://{settings.ALLOWED_HOSTS[0]}{reverse_lazy('payment:evotor', kwargs={'pk': instance.id})}"},
# #             "receipt": {
# #                 "client": {
# #                     "email": instance.user.email if instance.user else None,
# #                     "phone": str(instance.user.username) if instance.user else None,
# #                 },
# #                 "company": {
# #                     "email": settings.PAYMENT_EMAIL,
# #                     "sno": settings.SNO,
# #                     "inn": settings.INN,
# #                     "payment_address": settings.ALLOWED_HOSTS[0],
# #                 },
# #                 "items": [ReceiptLineSerializer(line).data for line in instance.lines.all()],
# #                 "payments": [
# #                     {"type": 0 if src.reference in settings.CASH_PAYMENTS else 1, "sum": src.amount_allocated}
# #                     for src in instance.sources.all()
# #                 ],
# #                 "total": instance.total,
# #             },
# #         }

# #         if instance.shipping > 0:
# #             representation["items"].append({
# #                 "name": "Доставка",
# #                 "price": instance.shipping,
# #                 "quantity": 1,
# #                 "measure": 0,
# #                 "sum": instance.shipping,
# #                 "payment_method": "full_payment",
# #                 "payment_object": 4,
# #                 "vat": {"type": "vat20"},
# #             })

# #         return representation


# # ================= запросы к терминалам (Отправка заказов) =================


# # class EvotorAPIMobileCashier:
# #     """ "
# #     Документация для внедрения по ссылке ниже

# #     ТОКЕН МОБИЛЬНОГО КАССИРА (Для отправки запросов к текрминалам)

# #     """

# #     def __init__(
# #         self, base_url: str = "https://fiscalization-test.evotor.ru/possystem/v5/"
# #     ):
# #         """
# #         Инициализация клиента для работы с API Эвотор Облако.

# #         :param api_token: Токен приложения для авторизации в API.
# #         :param base_url: Базовый URL для API. По умолчанию 'https://fiscalization.evotor.ru/possystem/v5/'. Для запросов к кассе
# #         """
# #         self.base_url = base_url
# #         self.headers = {
# #             "Content-Type": "application/json; charset=utf-8",
# #             "Accept": "application/json; charset=utf-8",
# #         }
# #         self.headers["Token"] = self.get_mobilecashier_token()

# #     def send_request(
# #         self, endpoint: str, method: str = "GET", data: dict = None, bulk: bool = False
# #     ):
# #         """
# #         Отправка HTTP-запроса к Эвотор API.

# #         :param endpoint: Конечная точка API (без базового URL).
# #         :param method: HTTP-метод (GET, POST, PUT, DELETE).
# #         :param data: Данные для отправки в теле запроса (для методов POST/PUT).
# #         :return: Ответ от API в формате JSON.
# #         """
# #         url = self.base_url + endpoint

# #         if bulk:
# #             self.headers["Content-Type"] = "application/vnd.evotor.v2+bulk+json"
# #         else:
# #             self.headers["Content-Type"] = "application/vnd.evotor.v2+json"

# #         try:
# #             if method == "GET":
# #                 response = requests.get(url, headers=self.headers)
# #             elif method == "POST":
# #                 response = requests.post(url, headers=self.headers, json=data)
# #             elif method == "PUT":
# #                 response = requests.put(url, headers=self.headers, json=data)
# #             elif method == "PATCH":
# #                 response = requests.patch(url, headers=self.headers, json=data)
# #             elif method == "DELETE":
# #                 response = requests.delete(url, headers=self.headers)
# #             else:
# #                 logger.error(f"Ошибка HTTP запроса. Неизвестный http метод: {method}")
# #                 raise ValueError(f"Unsupported HTTP method: {method}")

# #             response.raise_for_status()  # Проверка на успешный статус запроса (2xx)
# #             return response.json()  # Возврат данных в формате JSON

# #         except requests.exceptions.HTTPError as http_err:
# #             error = ""
# #             if response.status_code == 400:
# #                 error = "Неверный запрос Эвотор."
# #             if response.status_code == 401:
# #                 error = "Ошибка авторизации приложения Эвотор."
# #             elif response.status_code == 402:
# #                 error = (
# #                     "Приложение Эвотор не установлено на одно или несколько устройств."
# #                 )
# #             elif response.status_code == 403:
# #                 error = "Нет доступа Эвотор. Ошибка возникает когда у приложения нет разрешения на запрашиваемое действие или пользователь не установил приложение в Личном кабинете."
# #             elif response.status_code == 404:
# #                 error = "Запрашиваемый ресурс не найден в Эвотор."
# #             elif response.status_code == 405:
# #                 error = "Недопустимый метод запроса в Эвотор."
# #             elif response.status_code == 406:
# #                 error = "Тип содержимого, которое возвращает ресурс не соответствует типу содержимого, которое указанно в заголовке Accept Эвотор."
# #             elif response.status_code == 429:
# #                 error = "Превышено максимальное количество запросов Эвотор в текущем периоде."
# #             logger.error(f"Ошибка HTTP запроса при отправке Эвотор запроса: {http_err}")
# #             return {"error": error}
# #         except Exception as err:
# #             if response.status_code == 204:
# #                 return {}
# #             logger.error(f"Ошибка при отправке Эвотор запроса: {err}")
# #             return {"error": f"Ошибка при отправке Эвотор запроса: {err}"}

# #     def get_mobilecashier_token(self):

# #         cashier_token = CRMMobileCashierToken.objects.first()
# #         current_time = now()

# #         if cashier_token and (current_time - cashier_token.created_at) < timedelta(
# #             hours=23
# #         ):
# #             return cashier_token.token
# #         else:
# #             if cashier_token:
# #                 cashier_token.delete()

# #             auth_data = {"login": cashier_login, "pass": cashier_pass}

# #             endpoint = f"getToken"
# #             response = self.send_request(endpoint, "POST", auth_data)

# #             token = response.get("token", None)

# #             if token is not None:
# #                 CRMMobileCashierToken.objects.create(token=token)

# #             return token


# # class EvotorMobileCashier(EvotorAPIMobileCashier):

# #     def send_order(self, order_json):
# #         """
# #         Регистрация чека с операцией «Приход»
# #         https://docs.evotor.online/api/opisanie-api-konnektor-atol-onlain

# #         """
# #         endpoint = f"{cashier_group_code}/sell"
# #         response = self.send_request(endpoint, "POST", order_json)
# #         error = response.get("error", None) if isinstance(response, dict) else None

# #         if not error:
# #             order_id = order_json.get("external_id", None)
# #             if order_id:
# #                 order = Order.objects.get(id=order_id)
# #                 order.evotor_id = response.get("uuid")
# #                 order.save()

# #     def cancel_order(self, order_json):
# #         """
# #         https://mobilecashier.ru/api/v4/asc/create/{userId}
# #         """
# #         endpoint = f"<group_code>/sell_refund"
# #         response = self.send_request(endpoint, "POST", order_json)
# #         error = response.get("error", None) if isinstance(response, dict) else None

# #         # if not error:
# #             # order.refund


# # ================= запросы к АТОЛ Онлайн (Отправка чеков) =================


# # class EvotorAPIATOL:
# #     """ "
# #     Документация для внедрения по ссылке ниже

# #     ТОКЕН МОБИЛЬНОГО КАССИРА (Для отправки запросов к текрминалам)

# #     """

# #     def __init__(
# #         self, base_url: str = "https://fiscalization-test.evotor.ru/possystem/v5/"
# #     ):
# #         """
# #         Инициализация клиента для работы с API Эвотор Облако.

# #         :param api_token: Токен приложения для авторизации в API.
# #         :param base_url: Базовый URL для API. По умолчанию 'https://fiscalization.evotor.ru/possystem/v5/'. Для запросов к кассе
# #         """
# #         self.base_url = base_url
# #         self.headers = {
# #             "Content-Type": "application/json; charset=utf-8",
# #             "Accept": "application/json; charset=utf-8",
# #         }
# #         self.headers["Token"] = self.get_mobilecashier_token()

# #     def send_request(
# #         self, endpoint: str, method: str = "GET", data: dict = None, bulk: bool = False
# #     ):
# #         """
# #         Отправка HTTP-запроса к Эвотор API.

# #         :param endpoint: Конечная точка API (без базового URL).
# #         :param method: HTTP-метод (GET, POST, PUT, DELETE).
# #         :param data: Данные для отправки в теле запроса (для методов POST/PUT).
# #         :return: Ответ от API в формате JSON.
# #         """
# #         url = self.base_url + endpoint

# #         if bulk:
# #             self.headers["Content-Type"] = "application/vnd.evotor.v2+bulk+json"
# #         else:
# #             self.headers["Content-Type"] = "application/vnd.evotor.v2+json"

# #         try:
# #             if method == "GET":
# #                 response = requests.get(url, headers=self.headers)
# #             elif method == "POST":
# #                 response = requests.post(url, headers=self.headers, json=data)
# #             elif method == "PUT":
# #                 response = requests.put(url, headers=self.headers, json=data)
# #             elif method == "PATCH":
# #                 response = requests.patch(url, headers=self.headers, json=data)
# #             elif method == "DELETE":
# #                 response = requests.delete(url, headers=self.headers)
# #             else:
# #                 logger.error(f"Ошибка HTTP запроса. Неизвестный http метод: {method}")
# #                 raise ValueError(f"Unsupported HTTP method: {method}")

# #             response.raise_for_status()  # Проверка на успешный статус запроса (2xx)
# #             return response.json()  # Возврат данных в формате JSON

# #         except requests.exceptions.HTTPError as http_err:
# #             error = ""
# #             if response.status_code == 400:
# #                 error = "Неверный запрос Эвотор."
# #             if response.status_code == 401:
# #                 error = "Ошибка авторизации приложения Эвотор."
# #             elif response.status_code == 402:
# #                 error = (
# #                     "Приложение Эвотор не установлено на одно или несколько устройств."
# #                 )
# #             elif response.status_code == 403:
# #                 error = "Нет доступа Эвотор. Ошибка возникает когда у приложения нет разрешения на запрашиваемое действие или пользователь не установил приложение в Личном кабинете."
# #             elif response.status_code == 404:
# #                 error = "Запрашиваемый ресурс не найден в Эвотор."
# #             elif response.status_code == 405:
# #                 error = "Недопустимый метод запроса в Эвотор."
# #             elif response.status_code == 406:
# #                 error = "Тип содержимого, которое возвращает ресурс не соответствует типу содержимого, которое указанно в заголовке Accept Эвотор."
# #             elif response.status_code == 429:
# #                 error = "Превышено максимальное количество запросов Эвотор в текущем периоде."
# #             logger.error(f"Ошибка HTTP запроса при отправке Эвотор запроса: {http_err}")
# #             return {"error": error}
# #         except Exception as err:
# #             if response.status_code == 204:
# #                 return {}
# #             logger.error(f"Ошибка при отправке Эвотор запроса: {err}")
# #             return {"error": f"Ошибка при отправке Эвотор запроса: {err}"}

# #     def get_mobilecashier_token(self):

# #         cashier_token = CRMMobileCashierToken.objects.first()
# #         current_time = now()

# #         if cashier_token and (current_time - cashier_token.created_at) < timedelta(
# #             hours=23
# #         ):
# #             return cashier_token.token
# #         else:
# #             if cashier_token:
# #                 cashier_token.delete()

# #             auth_data = {"login": cashier_login, "pass": cashier_pass}

# #             endpoint = f"getToken"
# #             response = self.send_request(endpoint, "POST", auth_data)

# #             token = response.get("token", None)

# #             if token is not None:
# #                 CRMMobileCashierToken.objects.create(token=token)

# #             return token


# # class EvotorATOL(EvotorAPIATOL):

# #     def sell(self, order_json):
# #         """
# #         Регистрация чека с операцией «Приход»
# #         https://docs.evotor.online/api/opisanie-api-konnektor-atol-onlain

# #         """
# #         endpoint = f"{cashier_group_code}/sell"
# #         response = self.send_request(endpoint, "POST", order_json)
# #         error = response.get("error", None) if isinstance(response, dict) else None

# #         if not error:
# #             order_id = order_json.get("external_id", None)
# #             if order_id:
# #                 order = Order.objects.get(id=order_id)
# #                 order.evotor_id = response.get("uuid")
# #                 order.save()

# #     def sell_refund(self, order_json):
# #         """
# #         https://mobilecashier.ru/api/v4/asc/create/{userId}
# #         """
# #         endpoint = f"<group_code>/sell_refund"
# #         response = self.send_request(endpoint, "POST", order_json)
# #         error = response.get("error", None) if isinstance(response, dict) else None

# #         # if not error:
# #             # order.refund

# #     def sell_correction(self, order_json):
# #         """
# #         https://mobilecashier.ru/api/v4/asc/create/{userId}
# #         """
# #         endpoint = f"<group_code>/sell_refund"
# #         response = self.send_request(endpoint, "POST", order_json)
# #         error = response.get("error", None) if isinstance(response, dict) else None

# #         # if not error:
# #             # order.update

# #     def sell_refund_correction(self, order_json):
# #         """
# #         https://mobilecashier.ru/api/v4/asc/create/{userId}
# #         """
# #         endpoint = f"<group_code>/sell_refund_correction"
# #         response = self.send_request(endpoint, "POST", order_json)
# #         error = response.get("error", None) if isinstance(response, dict) else None

# #         # if not error:
# #             # order.update


#     # сырые данные

#     # oid = 'номер операции в вашем магазине'
#     # intent = Intent.SELL  # Направление платежа
#     # # Используйте Intent.RETURN для оформления возврата

#     # check = Check(oid, intent)

#     # email = 'client@client.ru'   # E-Mail пользователя для отправки электронного чека
#     # phone = '+79992400041'       # Телефон пользователя
#     # name = 'Иванов Иван'         # Имя пользователя
#     # inn = '5834041042'           # Инн пользователя

#     # check.set_client(email=email, phone=phone, name=name, inn=inn)

#     # payment_address = 'www.shop.com'   # Платёжный адрес организации

#     # # Система налогооблажения
#     # tax_system = TaxSystem.COMMON  # ОСН
#     # # tax_system = TaxSystem.SIMPLIFIED_IN  # УСН доход
#     # # tax_system = TaxSystem.SIMPLIFIED_IN_OUT  # УСН доход - расход
#     # # tax_system = TaxSystem.UTOII  # ЕНВД
#     # # tax_system = TaxSystem.UST  # ЕСН
#     # # tax_system = TaxSystem.PATENT  # Патент

#     # check.set_company(payment_address=payment_address, tax_system=tax_system)

#     # position_name = 'Наименование позиции'
#     # position_price = 100  # Цена позиции

#     # # Единицы измерений
#     # measure = MeasureTypes.PIECE
#     # # measure = MeasureTypes.PIECE
#     # # measure = MeasureTypes.GRAMM
#     # # measure = MeasureTypes.KILOGRAMM
#     # # measure = MeasureTypes.TON
#     # # measure = MeasureTypes.CENTIMETER
#     # # measure = MeasureTypes.DECIMETER
#     # # measure = MeasureTypes.METER
#     # # measure = MeasureTypes.SQUARE_CENTIMETER
#     # # measure = MeasureTypes.SQUARE_DECIMETER
#     # # measure = MeasureTypes.SQUARE_METER
#     # # measure = MeasureTypes.MILLILITER
#     # # measure = MeasureTypes.LITER
#     # # measure = MeasureTypes.CUBIC_METER
#     # # measure = MeasureTypes.KILOWATT_HOUR
#     # # measure = MeasureTypes.GIGA_CALORIE
#     # # measure = MeasureTypes.DAY
#     # # measure = MeasureTypes.HOUR
#     # # measure = MeasureTypes.MINUTE
#     # # measure = MeasureTypes.SECOND
#     # # measure = MeasureTypes.KILOBYTE
#     # # measure = MeasureTypes.MEGABYTE
#     # # measure = MeasureTypes.GIGABYTE
#     # # measure = MeasureTypes.TERABYTE
#     # # measure = MeasureTypes.OTHER_MEASURMENTS

#     # # Налоговая ставка
#     # vat_rate = VatRate.RATE_NO  # Без НДС
#     # # vat_rate = VatRate.RATE_0  # НДС 0%
#     # # vat_rate = VatRate.RATE_5  # НДС 5%
#     # # vat_rate = VatRate.RATE_7  # НДС 7%
#     # # vat_rate = VatRate.RATE_10  # НДС 10%
#     # # vat_rate = VatRate.RATE_20  # НДС 20%
#     # # vat_rate = VatRate.RATE_105  # НДС 5/105
#     # # vat_rate = VatRate.RATE_107  # НДС 7/107
#     # # vat_rate = VatRate.RATE_110  # НДС 10/110
#     # # vat_rate = VatRate.RATE_120  # НДС 20/120

#     # #Способ расчёта
#     # payment_method = PaymentMethod.PRE_PAYMENT_FULL
#     # # payment_method = PaymentMethod.PRE_PAYMENT_PART
#     # # payment_method = PaymentMethod.FULL_PAYMENT
#     # # payment_method = PaymentMethod.ADVANCE
#     # # payment_method = PaymentMethod.CREDIT_PART
#     # # payment_method = PaymentMethod.CREDIT_PAY
#     # # payment_method = PaymentMethod.CREDIT


#     # # Признак рассчета
#     # payment_object = PaymentObject.PRODUCT
#     # # payment_object = PaymentObject.PRODUCT_PRACTICAL
#     # # payment_object = PaymentObject.WORK
#     # # payment_object = PaymentObject.SERVICE
#     # # payment_object = PaymentObject.GAMBLING_BET
#     # # payment_object = PaymentObject.GAMBLING_WIN
#     # # payment_object = PaymentObject.LOTTERY_BET
#     # # payment_object = PaymentObject.LOTTERY_WIN
#     # # payment_object = PaymentObject.RID
#     # # payment_object = PaymentObject.PAYMENT
#     # # payment_object = PaymentObject.COMMISSION
#     # # payment_object = PaymentObject.COMPOSITE
#     # # payment_object = PaymentObject.PAY
#     # # payment_object = PaymentObject.OTHER
#     # # payment_object = PaymentObject.PROPERTY_RIGHT
#     # # payment_object = PaymentObject.NON_OPERATING
#     # # payment_object = PaymentObject.INSURANCE
#     # # payment_object = PaymentObject.SALES_TAX
#     # # payment_object = PaymentObject.RESORT_FEE
#     # # payment_object = PaymentObject.DEPOSIT
#     # # payment_object = PaymentObject.CONSUMPTION
#     # # payment_object = PaymentObject.SOLE_PROPRIETOR_CPI_CONTRIBUTINS
#     # # payment_object = PaymentObject.CPI_CONTRIBUTINS
#     # # payment_object = PaymentObject.SOLE_PROPRIETOR_CMI_CONTRIBUTINS
#     # # payment_object = PaymentObject.CMI_CONTRIBUTINS
#     # # payment_object = PaymentObject.CSI_CONTRIBUTINS
#     # # payment_object = PaymentObject.CASINO_PAYMENT
#     # # payment_object = PaymentObject.PAYMENT_OF_THE_MONEY
#     # # payment_object = PaymentObject.ATHM
#     # # payment_object = PaymentObject.ATM
#     # # payment_object = PaymentObject.THM
#     # # payment_object = PaymentObject.TM

#     # # Создание позиции
#     # position = Position(id=1,  # Идентификатор позиции в магазине
#     #                     name='Наименование позиции',
#     #                     price=10, # Цена за единицу
#     #                     quantity=1,  # Количество единиц
#     #                     total=10, # Общая стоимость позиции
#     #                     excise=10, # Акциз
#     #                     measure=measure, # Единица измерения
#     #                     user_data='Дополнительный реквизит предмета расчета',
#     #                     payment_method=payment_method, # Метод расчёта
#     #                     vat=vat_rate,  # Тип налога
#     #                     payment_object=payment_object # Объект расчёта
#     # )

#     # # Типы маркировок
#     # mark_type = MarkTypes.EAN13
#     # # mark_type = MarkTypes.UNKNOWN
#     # # mark_type = MarkTypes.EAN8
#     # # mark_type = MarkTypes.ITF14
#     # # mark_type = MarkTypes.GS10
#     # # mark_type = MarkTypes.GS1M
#     # # mark_type = MarkTypes.GS10
#     # # mark_type = MarkTypes.SHORT
#     # # mark_type = MarkTypes.FUR
#     # # mark_type = MarkTypes.EGAIS20
#     # # mark_type = MarkTypes.EGAIS30

#     # # Добавление кода маркировки в позицию
#     # position.set_mark_code(type=mark_type, code='1234567890123')

#     # # Установка дробности маркированного товара
#     # position.set_mark_quantity(numerator=1, denominator=2)

#     # # Если нужна информация о агенте

#     # # Создание агента
#     # agent_info = Agent(agent_type=AgentType.AGENT, phone='+79998887766',
#     #                     name='Названиепоставщика', inn='287381373424')

#     # # Если нужно, установка платёжного агента
#     # agent_info.set_paying_agent(operation='Операция1', phones=['+79998887766'])

#     # # Если нужно, установка оператора приёма платежей
#     # agent_info.set_receive_payments_operator(phones=['+79998887766'])

#     # # Если нужно, установка оператора перевода средств
#     # agent_info.set_money_transfer_operator(phones=['+79998887766'], name='Операторперевода',
#     #                                         address='г. Москва, ул. Складочная д.3',
#     #                                         inn='8634330204')

#     # # Добавление агента в позицию
#     # position.set_agent(agent_info)

#     # # Добавление позиции
#     # check.add_position(position)

#     # # Добавление суммы расчёта
#     # check.add_payment(300)

#     # # Если нужно распечатать чек (по умолчанию False)
#     # check.set_print(True)

#     # # Если нужно задать данные по кассиру, по умолчанию возьмутся с ФН
#     # check.set_cashier('Иваров И.П.', '1234567890123')

#     # # Если нужно установить дополнительные параметры чека
#     # check.set_additional_check_props('445334544')

#     # # Если нужно получитиь отчёт об успешной фискализации
#     # check.set_callback_url('http://shop.pro/fiscal_check/callback')

#     # # Отправка запроса
#     # try:
#     #     task = client.create_task(check, 'идентификатор очереди')
#     # except HTTPError as exc:
#     #     print(exc.response.text)
#     # else:
#     #     print(task)
#     # # Task(id=1, external_id=2, print_queue_id=3, state='new')
#     # # id - идентификатор задачи
#     # # external_id - идентификатор операции в магазине
#     # # print_queue_id - идентификатор очереди
#     # # state - состояние задачи


#     # # Создание чека коррекции

#     # intent = Intent.SELL_CORRECTION  # Коррекция прихода
#     # # intent = Intent.BUY_CORRECTION # Коррекция расхода
#     # # intent = Intent.SELL_RETURN_CORRECTION # Коррекция возврата прихода
#     # # intent = Intent.BUY_RETURN_CORRECTION # Коррекция возврата расхода

#     # check = CorrectionCheck(oid, intent)

#     # # Установка данных компании
#     # check.set_company(payment_address=payment_address, tax_system=tax_system)

#     # payment_type = PaymentType.CARD # Тип оплаты, корректирующей суммы
#     # # payment_method = PaymentType.CARD # электронные
#     # # payment_method = PaymentType.CASH # наличные

#     # # Установка суммы коррекции
#     # check.add_payment(12, payment_type)

#     # correction_type = CorrectionType.SELF # Тип коррекции
#     # # correction_type = CorrectionType.SELF # Самостоятельно
#     # # correction_type = CorrectionType.FORCED # По предписанию

#     # # Установка данных коррекции
#     # check.set_correction_info(correction_type,
#     #                         '31.03.2022', # Дата документа коррекции в формате 'dd.mm.yyyy'
#     #                         'K11',        # Номер документа коррекции
#     # )

#     # # Создаём позицию коррекции
#     # position = Position(name='Товар', price=10, quantity=5, total=50,
#     #                     measure=measure, payment_method=payment_method,
#     #                     payment_object=payment_object, vat=vat_rate)

#     # # Добавляем позицию коррекции
#     # check.add_position(position)

#     # # Указание уполномоченного лица
#     # check.set_authorised_person(
#     #     name='Иванов И.И',
#     #     inn='123456789012'
#     # )

#     # # Если нужно получитиь отчёт об успешной фискализации
#     # check.set_callback_url('http://shop.pro/fiscal_check/callback')

#     # # Отправка запроса
#     # try:
#     #     task = client.create_task(check, 'идентификатор очереди')
#     # except HTTPError as exc:
#     #     print(exc.response.text)
#     # else:
#     #     print(task)
#     # # Task(id=1, external_id=2, print_queue_id=3, state='new')
#     # # id - идентификатор задачи
#     # # external_id - идентификатор операции в магазине
#     # # print_queue_id - идентификатор очереди
#     # # state - состояние задачи

#     # # Получение информации о поставленной на фискализацию задаче:
#     # try:
#     #     task_info = client.get_task_info('идентификатор задачи')
#     # except HTTPError as exc:
#     #     print(exc.response.text)
#     # else:
#     #     print(task_info)
#     # # TaskInfo(id=234, external_id='4321', state='done', error_description=None,
#     # #          fiscal_data={'i': '111',
#     # #                       'fn': '2222222222222222',
#     # #                       't': '3333333333333',
#     # #                       'n': 4,
#     # #                       'fp': '555555555',
#     # #                       's': '6666.77'})
#     # # id - идентификатор задачи
#     # # external_id - идентификатор операции в магазине
#     # # state - состояние задачи
#     # # error_description - описание возникшей ошибки, когда state=='error'
#     # # fiscal_data - фискальные данные


#     # # Чтобы проверить, является ли очередь активной, выполните:
#     # client.is_queue_active('идентификатор очереди')

#     # # Вы можете указать идентификатор очереди по умолчанию с помощью:
#     # client.set_default_queue('идентификатор очереди по умолчанию')
#     # # В этом случае можно не указывать идентификатор очереди всякий раз,
#     # # когда нужно распечатать чек или проверить состояние очереди:
#     # assert client.is_queue_active() is True
#     # try:
#     #     task = client.create_task(check)
#     # except HTTPError as exc:
#     #     print(exc.response.text)
#     # else:
#     #     print(task)


# # ================= запросы к терминалам (Отправка заказов) =================


# # class EvotorAPIMobileCashier:
# #     """ "
# #     Документация для внедрения по ссылке ниже

# #     ТОКЕН МОБИЛЬНОГО КАССИРА (Для отправки запросов к текрминалам)

# #     """

# #     def __init__(
# #         self, base_url: str = "https://fiscalization-test.evotor.ru/possystem/v5/"
# #     ):
# #         """
# #         Инициализация клиента для работы с API Эвотор Облако.

# #         :param api_token: Токен приложения для авторизации в API.
# #         :param base_url: Базовый URL для API. По умолчанию 'https://fiscalization.evotor.ru/possystem/v5/'. Для запросов к кассе
# #         """
# #         self.base_url = base_url
# #         self.headers = {
# #             "Content-Type": "application/json; charset=utf-8",
# #             "Accept": "application/json; charset=utf-8",
# #         }
# #         self.headers["Token"] = self.get_mobilecashier_token()

# #     def send_request(
# #         self, endpoint: str, method: str = "GET", data: dict = None, bulk: bool = False
# #     ):
# #         """
# #         Отправка HTTP-запроса к Эвотор API.

# #         :param endpoint: Конечная точка API (без базового URL).
# #         :param method: HTTP-метод (GET, POST, PUT, DELETE).
# #         :param data: Данные для отправки в теле запроса (для методов POST/PUT).
# #         :return: Ответ от API в формате JSON.
# #         """
# #         url = self.base_url + endpoint

# #         if bulk:
# #             self.headers["Content-Type"] = "application/vnd.evotor.v2+bulk+json"
# #         else:
# #             self.headers["Content-Type"] = "application/vnd.evotor.v2+json"

# #         try:
# #             if method == "GET":
# #                 response = requests.get(url, headers=self.headers)
# #             elif method == "POST":
# #                 response = requests.post(url, headers=self.headers, json=data)
# #             elif method == "PUT":
# #                 response = requests.put(url, headers=self.headers, json=data)
# #             elif method == "PATCH":
# #                 response = requests.patch(url, headers=self.headers, json=data)
# #             elif method == "DELETE":
# #                 response = requests.delete(url, headers=self.headers)
# #             else:
# #                 logger.error(f"Ошибка HTTP запроса. Неизвестный http метод: {method}")
# #                 raise ValueError(f"Unsupported HTTP method: {method}")

# #             response.raise_for_status()  # Проверка на успешный статус запроса (2xx)
# #             return response.json()  # Возврат данных в формате JSON

# #         except requests.exceptions.HTTPError as http_err:
# #             error = ""
# #             if response.status_code == 400:
# #                 error = "Неверный запрос Эвотор."
# #             if response.status_code == 401:
# #                 error = "Ошибка авторизации приложения Эвотор."
# #             elif response.status_code == 402:
# #                 error = (
# #                     "Приложение Эвотор не установлено на одно или несколько устройств."
# #                 )
# #             elif response.status_code == 403:
# #                 error = "Нет доступа Эвотор. Ошибка возникает когда у приложения нет разрешения на запрашиваемое действие или пользователь не установил приложение в Личном кабинете."
# #             elif response.status_code == 404:
# #                 error = "Запрашиваемый ресурс не найден в Эвотор."
# #             elif response.status_code == 405:
# #                 error = "Недопустимый метод запроса в Эвотор."
# #             elif response.status_code == 406:
# #                 error = "Тип содержимого, которое возвращает ресурс не соответствует типу содержимого, которое указанно в заголовке Accept Эвотор."
# #             elif response.status_code == 429:
# #                 error = "Превышено максимальное количество запросов Эвотор в текущем периоде."
# #             logger.error(f"Ошибка HTTP запроса при отправке Эвотор запроса: {http_err}")
# #             return {"error": error}
# #         except Exception as err:
# #             if response.status_code == 204:
# #                 return {}
# #             logger.error(f"Ошибка при отправке Эвотор запроса: {err}")
# #             return {"error": f"Ошибка при отправке Эвотор запроса: {err}"}

# #     def get_mobilecashier_token(self):

# #         cashier_token = CRMMobileCashierToken.objects.first()
# #         current_time = now()

# #         if cashier_token and (current_time - cashier_token.created_at) < timedelta(
# #             hours=23
# #         ):
# #             return cashier_token.token
# #         else:
# #             if cashier_token:
# #                 cashier_token.delete()

# #             auth_data = {"login": cashier_login, "pass": cashier_pass}

# #             endpoint = f"getToken"
# #             response = self.send_request(endpoint, "POST", auth_data)

# #             token = response.get("token", None)

# #             if token is not None:
# #                 CRMMobileCashierToken.objects.create(token=token)

# #             return token


# # class EvotorMobileCashier(EvotorAPIMobileCashier):

# #     def send_order(self, order_json):
# #         """
# #         Регистрация чека с операцией «Приход»
# #         https://docs.evotor.online/api/opisanie-api-konnektor-atol-onlain

# #         """
# #         endpoint = f"{cashier_group_code}/sell"
# #         response = self.send_request(endpoint, "POST", order_json)
# #         error = response.get("error", None) if isinstance(response, dict) else None

# #         if not error:
# #             order_id = order_json.get("external_id", None)
# #             if order_id:
# #                 order = Order.objects.get(id=order_id)
# #                 order.evotor_id = response.get("uuid")
# #                 order.save()

# #     def cancel_order(self, order_json):
# #         """
# #         https://mobilecashier.ru/api/v4/asc/create/{userId}
# #         """
# #         endpoint = f"<group_code>/sell_refund"
# #         response = self.send_request(endpoint, "POST", order_json)
# #         error = response.get("error", None) if isinstance(response, dict) else None

# #         # if not error:
# #             # order.refund


# # ================= запросы к АТОЛ Онлайн (Отправка чеков) =================


# # class EvotorAPIATOL:
# #     """ "
# #     Документация для внедрения по ссылке ниже

# #     ТОКЕН МОБИЛЬНОГО КАССИРА (Для отправки запросов к текрминалам)

# #     """

# #     def __init__(
# #         self, base_url: str = "https://fiscalization-test.evotor.ru/possystem/v5/"
# #     ):
# #         """
# #         Инициализация клиента для работы с API Эвотор Облако.

# #         :param api_token: Токен приложения для авторизации в API.
# #         :param base_url: Базовый URL для API. По умолчанию 'https://fiscalization.evotor.ru/possystem/v5/'. Для запросов к кассе
# #         """
# #         self.base_url = base_url
# #         self.headers = {
# #             "Content-Type": "application/json; charset=utf-8",
# #             "Accept": "application/json; charset=utf-8",
# #         }
# #         self.headers["Token"] = self.get_mobilecashier_token()

# #     def send_request(
# #         self, endpoint: str, method: str = "GET", data: dict = None, bulk: bool = False
# #     ):
# #         """
# #         Отправка HTTP-запроса к Эвотор API.

# #         :param endpoint: Конечная точка API (без базового URL).
# #         :param method: HTTP-метод (GET, POST, PUT, DELETE).
# #         :param data: Данные для отправки в теле запроса (для методов POST/PUT).
# #         :return: Ответ от API в формате JSON.
# #         """
# #         url = self.base_url + endpoint

# #         if bulk:
# #             self.headers["Content-Type"] = "application/vnd.evotor.v2+bulk+json"
# #         else:
# #             self.headers["Content-Type"] = "application/vnd.evotor.v2+json"

# #         try:
# #             if method == "GET":
# #                 response = requests.get(url, headers=self.headers)
# #             elif method == "POST":
# #                 response = requests.post(url, headers=self.headers, json=data)
# #             elif method == "PUT":
# #                 response = requests.put(url, headers=self.headers, json=data)
# #             elif method == "PATCH":
# #                 response = requests.patch(url, headers=self.headers, json=data)
# #             elif method == "DELETE":
# #                 response = requests.delete(url, headers=self.headers)
# #             else:
# #                 logger.error(f"Ошибка HTTP запроса. Неизвестный http метод: {method}")
# #                 raise ValueError(f"Unsupported HTTP method: {method}")

# #             response.raise_for_status()  # Проверка на успешный статус запроса (2xx)
# #             return response.json()  # Возврат данных в формате JSON

# #         except requests.exceptions.HTTPError as http_err:
# #             error = ""
# #             if response.status_code == 400:
# #                 error = "Неверный запрос Эвотор."
# #             if response.status_code == 401:
# #                 error = "Ошибка авторизации приложения Эвотор."
# #             elif response.status_code == 402:
# #                 error = (
# #                     "Приложение Эвотор не установлено на одно или несколько устройств."
# #                 )
# #             elif response.status_code == 403:
# #                 error = "Нет доступа Эвотор. Ошибка возникает когда у приложения нет разрешения на запрашиваемое действие или пользователь не установил приложение в Личном кабинете."
# #             elif response.status_code == 404:
# #                 error = "Запрашиваемый ресурс не найден в Эвотор."
# #             elif response.status_code == 405:
# #                 error = "Недопустимый метод запроса в Эвотор."
# #             elif response.status_code == 406:
# #                 error = "Тип содержимого, которое возвращает ресурс не соответствует типу содержимого, которое указанно в заголовке Accept Эвотор."
# #             elif response.status_code == 429:
# #                 error = "Превышено максимальное количество запросов Эвотор в текущем периоде."
# #             logger.error(f"Ошибка HTTP запроса при отправке Эвотор запроса: {http_err}")
# #             return {"error": error}
# #         except Exception as err:
# #             if response.status_code == 204:
# #                 return {}
# #             logger.error(f"Ошибка при отправке Эвотор запроса: {err}")
# #             return {"error": f"Ошибка при отправке Эвотор запроса: {err}"}

# #     def get_mobilecashier_token(self):

# #         cashier_token = CRMMobileCashierToken.objects.first()
# #         current_time = now()

# #         if cashier_token and (current_time - cashier_token.created_at) < timedelta(
# #             hours=23
# #         ):
# #             return cashier_token.token
# #         else:
# #             if cashier_token:
# #                 cashier_token.delete()

# #             auth_data = {"login": cashier_login, "pass": cashier_pass}

# #             endpoint = f"getToken"
# #             response = self.send_request(endpoint, "POST", auth_data)

# #             token = response.get("token", None)

# #             if token is not None:
# #                 CRMMobileCashierToken.objects.create(token=token)

# #             return token


# # class EvotorATOL(EvotorAPIATOL):

# #     def sell(self, order_json):
# #         """
# #         Регистрация чека с операцией «Приход»
# #         https://docs.evotor.online/api/opisanie-api-konnektor-atol-onlain

# #         """
# #         endpoint = f"{cashier_group_code}/sell"
# #         response = self.send_request(endpoint, "POST", order_json)
# #         error = response.get("error", None) if isinstance(response, dict) else None

# #         if not error:
# #             order_id = order_json.get("external_id", None)
# #             if order_id:
# #                 order = Order.objects.get(id=order_id)
# #                 order.evotor_id = response.get("uuid")
# #                 order.save()

# #     def sell_refund(self, order_json):
# #         """
# #         https://mobilecashier.ru/api/v4/asc/create/{userId}
# #         """
# #         endpoint = f"<group_code>/sell_refund"
# #         response = self.send_request(endpoint, "POST", order_json)
# #         error = response.get("error", None) if isinstance(response, dict) else None

# #         # if not error:
# #             # order.refund

# #     def sell_correction(self, order_json):
# #         """
# #         https://mobilecashier.ru/api/v4/asc/create/{userId}
# #         """
# #         endpoint = f"<group_code>/sell_refund"
# #         response = self.send_request(endpoint, "POST", order_json)
# #         error = response.get("error", None) if isinstance(response, dict) else None

# #         # if not error:
# #             # order.update

# #     def sell_refund_correction(self, order_json):
# #         """
# #         https://mobilecashier.ru/api/v4/asc/create/{userId}
# #         """
# #         endpoint = f"<group_code>/sell_refund_correction"
# #         response = self.send_request(endpoint, "POST", order_json)
# #         error = response.get("error", None) if isinstance(response, dict) else None

# #         # if not error:
# #             # order.update
