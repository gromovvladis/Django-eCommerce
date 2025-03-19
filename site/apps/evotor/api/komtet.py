import logging
from decimal import Decimal as D

from django.conf import settings
from django.urls import reverse_lazy
from komtet_kassa_sdk.v2 import (
    Agent,
    AgentType,
    Check,
    Client,
    CorrectionCheck,
    CorrectionType,
    Intent,
    MarkTypes,
    MeasureTypes,
    PaymentMethod,
    PaymentObject,
    PaymentType,
    Position,
    TaxSystem,
    VatRate,
)
from requests.exceptions import HTTPError

logger = logging.getLogger("apps.evotor")
callback_url = reverse_lazy("order:callback")

shop_id = ""
secret_key = ""

tax_system = settings.TAX_SYSTEM
payment_address = settings.ALLOWED_HOSTS[0]
payment_method = PaymentMethod.PRE_PAYMENT_FULL


class EvotorKomtet:

    unit_codes = {
        "шт": MeasureTypes.PIECE,
        "г": MeasureTypes.GRAMM,
        "кг": MeasureTypes.KILOGRAMM,
        "т": MeasureTypes.TON,
        "см": MeasureTypes.CENTIMETER,
        "дм": MeasureTypes.DECIMETER,
        "м": MeasureTypes.METER,
        "см²": MeasureTypes.SQUARE_CENTIMETER,
        "дм²": MeasureTypes.SQUARE_DECIMETER,
        "м²": MeasureTypes.SQUARE_METER,
        "мл": MeasureTypes.MILLILITER,
        "л": MeasureTypes.LITER,
        "м³": MeasureTypes.CUBIC_METER,
        "кВт·ч": MeasureTypes.KILOWATT_HOUR,
        "Гкал": MeasureTypes.KILOWATT_HOUR,
        "день": MeasureTypes.DAY,
        "час": MeasureTypes.HOUR,
        "минута": MeasureTypes.MINUTE,
        "секунда": MeasureTypes.SECOND,
        "КБ": MeasureTypes.KILOBYTE,
        "МБ": MeasureTypes.MEGABYTE,
        "ГБ": MeasureTypes.GIGABYTE,
        "ТБ": MeasureTypes.TERABYTE,
    }

    vats = {
        "none": VatRate.RATE_NO,
        "vat0": VatRate.RATE_0,
        "vat10": VatRate.RATE_10,
        "vat110": VatRate.RATE_110,
        "vat20": VatRate.RATE_20,
        "vat120": VatRate.RATE_120,
    }

    # Receipt

    def create_check(self, order_json):
        client = Client(shop_id, secret_key)

        lines = order_json.get("lines")
        user = order_json.get("user")

        check = Check(order_json.get("number"), Intent.SELL)
        check.set_client(email=user.get("email"), phone=user.get("username"))
        check.set_company(payment_address=payment_address, tax_system=tax_system)

        for line in lines:
            check.add_position(
                Position(
                    id=line.get("evotor_id"),
                    name=line.get("name"),
                    price=line.get("unit_price"),  # Цена за единицу
                    quantity=line.get("quantity"),  # Количество единиц
                    total=line.get("line_price"),  # Общая стоимость позиции
                    measure=self.unit_codes.get(
                        line.get("measure_name"), MeasureTypes.PIECE
                    ),  # Единица измерения
                    payment_method=payment_method,  # Метод расчёта
                    vat=self.unit_codes.get(
                        line.get("vat"), VatRate.RATE_NO
                    ),  # Тип налога
                    payment_object=PaymentObject.PRODUCT,  # Объект расчёта
                )
            )

        sipping_price = D(order_json.get("shipping"))
        if sipping_price > 0:
            check.add_position(
                Position(
                    name="Доставка",
                    price=sipping_price,  # Цена за единицу
                    quantity=1,  # Количество единиц
                    total=sipping_price,  # Общая стоимость позиции
                    measure=MeasureTypes.OTHER_MEASURMENTS,  # Единица измерения
                    payment_method=payment_method,  # Метод расчёта
                    vat=VatRate.RATE_20,  # переделай, Тип налога
                    payment_object=PaymentObject.SERVICE,  # Объект расчёта
                )
            )

        check.add_payment(order_json.get("amount_allocated"))
        check.set_print(False)
        check.set_callback_url(f"https://{payment_address}{callback_url}")

        try:
            client.create_task(check)
        except HTTPError as exc:
            logger.error(
                f"Ошибка при отправке заказа в очередь КОМТЕТ: {exc.response.text}"
            )

    def refund_check(self, order_json):
        pass

    # Order Evotor

    def create_order(self, order_json):
        lines = order_json.get("lines")
        user = order_json.get("user")

        check = Check(order_json.get("number"), Intent.SELL)
        check.set_client(email=user.get("email"), phone=user.get("username"))
        check.set_company(payment_address=payment_address, tax_system=tax_system)

        for line in lines:
            check.add_position(
                Position(
                    id=line.get("evotor_id"),
                    name=line.get("name"),
                    price=line.get("unit_price"),  # Цена за единицу
                    quantity=line.get("quantity"),  # Количество единиц
                    total=line.get("line_price"),  # Общая стоимость позиции
                    measure=self.unit_codes.get(
                        line.get("measure_name"), MeasureTypes.PIECE
                    ),  # Единица измерения
                    payment_method=payment_method,  # Метод расчёта
                    vat=self.unit_codes.get(
                        line.get("vat"), VatRate.RATE_NO
                    ),  # Тип налога
                    payment_object=PaymentObject.PRODUCT,  # Объект расчёта
                )
            )

        sipping_price = D(order_json.get("shipping"))
        if sipping_price > 0:
            check.add_position(
                Position(
                    name="Доставка",
                    price=sipping_price,  # Цена за единицу
                    quantity=1,  # Количество единиц
                    total=sipping_price,  # Общая стоимость позиции
                    measure=MeasureTypes.OTHER_MEASURMENTS,  # Единица измерения
                    payment_method=payment_method,  # Метод расчёта
                    vat=VatRate.RATE_20,  # переделай, Тип налога
                    payment_object=PaymentObject.SERVICE,  # Объект расчёта
                )
            )

        check.add_payment(order_json.get("amount_allocated"))
        check.set_print(False)
        check.set_callback_url(f"https://{payment_address}{callback_url}")

        try:
            client.create_task(check)
        except HTTPError as exc:
            logger.error(f"Ошибка при отправке заказа: {exc.response.text}")

    def update_order(self, order_json):
        pass

    def delete_order(self, order_json):
        pass

    def order_info(self, order_json):
        pass

    # Employees

    def get_employees(self, order_json):
        pass

    def create_employee(self, order_json):
        pass

    def update_employee(self, order_json):
        pass

    def delete_employee(self, order_json):
        pass
