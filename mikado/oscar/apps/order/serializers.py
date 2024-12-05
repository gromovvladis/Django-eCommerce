import logging
from django.conf import settings
from rest_framework import serializers
from decimal import Decimal as D
from oscar.core.loading import get_model
from django.utils.timezone import now

logger = logging.getLogger("oscar.customer")

User = get_model("user", "User")
Store = get_model("store", "Store")
Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
StockRecord = get_model("store", "StockRecord")

Order = get_model("order", "Order")
OrderNote = get_model("order", "OrderNote")
OrderDiscount = get_model("order", "OrderDiscount")
OrderLineDiscount = get_model("order", "OrderLineDiscount")
Line = get_model("order", "Line")
LinePrice = get_model("order", "LinePrice")

Source = get_model("payment", "Source")
SourceType = get_model("payment", "SourceType")
Transaction = get_model("payment", "Transaction")


class OrderSerializer(serializers.Serializer):
    id = serializers.CharField(source="evotor_id")
    number = serializers.IntegerField(write_only=True)
    store_id = serializers.CharField(write_only=True)

    created_at = serializers.DateTimeField(write_only=True)

    extras = serializers.DictField(write_only=True, required=False)
    body = serializers.DictField(write_only=True)

    class Meta:
        model = Order
        fields = ("id", "number", "store_id", "created_at", "extras", "body")

    def create(self, validated_data):

        evotor_id = validated_data.get("evotor_id")
        number = validated_data.get("number")
        store_id = validated_data.get("store_id")
        body = validated_data.get("body")

        extras = validated_data.get("extras", None)

        positions = body.get("positions", None)
        discounts = body.get("doc_discounts", None)
        payments = body.get("payments", None)
        result_sum = body.get("result_sum", None)
        customer_phone = body.get("customer_phone")

        user = None
        if customer_phone:
            user = User.objects.filter(username=customer_phone).first()

        store = Store.objects.get(evotor_id=store_id)

        order = Order.objects.create(
            number=(900000 + number),
            evotor_id=evotor_id,
            site="Эвотор",
            user=user,
            store=store,
            total=result_sum,
            shipping_method="Самовывоз",
            status=settings.OSCAR_FINAL_ORDER_STATUS,
            date_finish=now(),
            order_time=now(),
        )

        if extras:
            OrderNote.objects.create(
                order=order,
                note_type=OrderNote.STAFF,
                message=str(extras),
            )

        for position in positions:
            product, _ = Product.objects.get_or_create(
                evotor_id=position["product_id"],
                defaults={
                    "name": "Не созданый продукт",
                    "product_class": self._get_or_create_product_class(),
                },
            )
            stockrecord = product.stockrecords.filter(
                store__evotor_id=store_id, is_public=True
            )[0]
            line = Line.objects.create(
                order=order,
                store=store,
                name=product.get_name(),
                store_name=store.name,
                evotor_code=position["code"],
                product=product,
                stockrecord=stockrecord,
                quantity=position["quantity"],
                article=position["id"],
                line_price=D(position["result_price"]),
                line_price_before_discounts=D(position["sum"]),
                unit_price=D(position["price"]),
                tax_code=position["tax"]["type"],
            )

            LinePrice.objects.create(
                order=order,
                line=line,
                quantity=line.quantity,
                price=line.line_price,
                tax_code=line.tax_code,
            )

            position_discount = position["position_discount"]
            if position_discount:
                OrderLineDiscount(
                    line=line,
                    amount=position_discount["discount_sum"],
                )

        for payment in payments:
            source_type, _ = SourceType.objects.get_or_create(name=payment["type"])
            amount_debited = sum(
                D(part["part_sum"]) - D(part["change"]) for part in payment["parts"]
            )
            source = Source.objects.create(
                order=order,
                source_type=source_type,
                amount_debited=amount_debited,
                reference=payment["app_info"]["name"],
                refundable=False,
                paid=True,
            )
            Transaction.objects.create(
                source=source,
                txn_type="Payment",
                amount=D(payment["sum"]),
                reference=payment["app_info"]["name"],
                status="succeeded",
                paid=True,
                refundable=False,
                code=payment["id"],
                receipt=True,
            )

        if discounts:
            frequency_base = OrderDiscount.objects.filter(
                message="Скидка сотрудником"
            ).count()
            for i, discount in enumerate(discounts, start=1):
                OrderDiscount(
                    order=order,
                    message="Скидка сотрудником",
                    frequency=frequency_base + i,
                    amount=discount.get("discount_sum", 0),
                    voucher_code=discount.get("coupon", ""),
                )

        return order

    def _get_or_create_product_class(self):
        """Создание или извлечение класса товара"""
        return ProductClass.objects.get_or_create(
            name="Тип товара Эвотор",
            defaults={
                "track_stock": True,
                "requires_shipping": False,
                "measure_name": "шт",
            },
        )[0]


# request = {
#     "method": "PUT",
#     "path": "/crm/api/docs/",
#     "headers": {
#         "Host": "mikado-sushi.ru",
#         "X-Real-Ip": "185.170.204.77",
#         "X-Forwarded-For": "185.170.204.77",
#         "Connection": "close",
#         "Content-Length": "4049",
#         "Accept": "application/json, application/*+json",
#         "Content-Type": "application/json",
#         "Authorization": "Bearer 9179d780-56a4-49ea-b042-435e3257eaf8",
#         "X-Evotor-User-Id": "01-000000010409029",
#         "X-B3-Traceid": "55a9b800a95a346d",
#         "X-B3-Spanid": "2d67c50067b4031e",
#         "X-B3-Parentspanid": "55a9b800a95a346d",
#         "X-B3-Sampled": "0",
#         "User-Agent": "Java/1.8.0_151",
#     },
#     "data": {
#         "type": "SELL",
#         "id": "87e80c52-c459-4b44-ba3c-0c0c02552427",
#         "extras": {},
#         "number": 30749,
#         "close_date": "2024-12-05T04:47:15.000+0000",
#         "time_zone_offset": 25200000,
#         "session_id": "1c7f3686-5081-40e3-a501-827885e890f9",
#         "session_number": 149,
#         "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
#         "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
#         "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
#         "user_id": "01-000000010409029",
#         "body": {
#             "positions": [
#                 {
#                     "product_id": "dd94c895-5da8-435c-a6fe-1a64eec96fb2",
#                     "quantity": 1,
#                     "initial_quantity": -95,
#                     "quantity_in_package": null,
#                     "bar_code": null,
#                     "product_type": "NORMAL",
#                     "mark": null,
#                     "mark_data": null,
#                     "alcohol_by_volume": 0,
#                     "alcohol_product_kind_code": 0,
#                     "tare_volume": 0,
#                     "code": "23",
#                     "product_name": "Тортилья с семгой",
#                     "measure_name": "шт",
#                     "id": 237461,
#                     "uuid": "4b7aa459-f508-4a46-b086-64ede9ce9b54",
#                     "extra_keys": [],
#                     "sub_positions": [],
#                     "measure_precision": 0,
#                     "price": 320,
#                     "cost_price": 0,
#                     "result_price": 320,
#                     "sum": 320,
#                     "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
#                     "result_sum": 320,
#                     "position_discount": null,
#                     "doc_distributed_discount": null,
#                     "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                     "splitted_positions": null,
#                     "attributes_choices": null,
#                     "settlement_method": {"type": "CHECKOUT_FULL", "amount": null},
#                     "agent_requisites": null,
#                 },
#                 {
#                     "product_id": "e0b63c65-3f3c-46d3-a12a-725b79f23411",
#                     "quantity": 1,
#                     "initial_quantity": -91,
#                     "quantity_in_package": null,
#                     "bar_code": null,
#                     "product_type": "NORMAL",
#                     "mark": null,
#                     "mark_data": null,
#                     "alcohol_by_volume": 0,
#                     "alcohol_product_kind_code": 0,
#                     "tare_volume": 0,
#                     "code": "17",
#                     "product_name": "Кекс морковный",
#                     "measure_name": "шт",
#                     "id": 237463,
#                     "uuid": "fcd6e003-6cc9-484c-9a7b-ecab8fb69cb8",
#                     "extra_keys": [],
#                     "sub_positions": [],
#                     "measure_precision": 0,
#                     "price": 200,
#                     "cost_price": 0,
#                     "result_price": 200,
#                     "sum": 200,
#                     "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
#                     "result_sum": 200,
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
#                     "initial_quantity": -493,
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
#                     "id": 237465,
#                     "uuid": "04bf5f47-487d-47ae-a41a-6c03f2782326",
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
#                     "id": "f1a1477f-0c6c-4972-ab8d-409735086c25",
#                     "parent_id": null,
#                     "sum": 800,
#                     "type": "ELECTRON",
#                     "parts": [
#                         {
#                             "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                             "part_sum": 800,
#                             "change": 0,
#                         }
#                     ],
#                     "app_payment": null,
#                     "merchant_info": {
#                         "number": "123",
#                         "english_name": "123",
#                         "category_code": "123",
#                     },
#                     "bank_info": {"name": "ПАО СБЕРБАНК"},
#                     "app_info": {"app_id": null, "name": "Банковская карта"},
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
#                     "receipt_number": 39,
#                     "document_number": 41,
#                     "session_number": 148,
#                     "receipt_date": "05122024",
#                     "receipt_time": "1147",
#                     "fn_reg_number": null,
#                     "fiscal_sign_doc_number": "548426126",
#                     "fiscal_document_number": 30173,
#                     "fn_serial_number": "7382440700036332",
#                     "kkt_serial_number": "00307900652283",
#                     "kkt_reg_number": "0008200608019020",
#                     "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                     "check_sum": 800,
#                 }
#             ],
#             "sum": 800,
#             "result_sum": 800,
#             "customer_email": null,
#             "customer_phone": null,
#         },
#         "counterparties": null,
#         "created_at": "2024-12-05T04:47:16.581+0000",
#         "version": "V2",
#     },
# }


# request = {
#     "method": "PUT",
#     "path": "/crm/api/docs/",
#     "headers": {
#         "Host": "mikado-sushi.ru",
#         "X-Real-Ip": "185.170.204.77",
#         "X-Forwarded-For": "185.170.204.77",
#         "Connection": "close",
#         "Content-Length": "2508",
#         "Accept": "application/json, application/*+json",
#         "Content-Type": "application/json",
#         "Authorization": "Bearer 9179d780-56a4-49ea-b042-435e3257eaf8",
#         "X-Evotor-User-Id": "01-000000010409029",
#         "X-B3-Traceid": "2d7a322dbcab0f01",
#         "X-B3-Spanid": "e731b0918ff35ad2",
#         "X-B3-Parentspanid": "2d7a322dbcab0f01",
#         "X-B3-Sampled": "0",
#         "User-Agent": "Java/1.8.0_151",
#     },
#     "data": {
#         "type": "SELL",
#         "id": "54430aa6-7d5f-419e-bf26-1dc4c27f4316",
#         "extras": {},
#         "number": 30747,
#         "close_date": "2024-12-05T04:29:52.000+0000",
#         "time_zone_offset": 25200000,
#         "session_id": "1c7f3686-5081-40e3-a501-827885e890f9",
#         "session_number": 149,
#         "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
#         "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
#         "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
#         "user_id": "01-000000010409029",
#         "body": {
#             "positions": [
#                 {
#                     "product_id": "13111c38-e846-41f7-a723-7914a818eaac",
#                     "quantity": 1,
#                     "initial_quantity": -492,
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
#                     "id": 237447,
#                     "uuid": "4c1338c1-a104-4c65-ba72-8c234f141c5e",
#                     "extra_keys": [],
#                     "sub_positions": [],
#                     "measure_precision": 0,
#                     "price": 280,
#                     "cost_price": 0,
#                     "result_price": 140,
#                     "sum": 280,
#                     "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
#                     "result_sum": 140,
#                     "position_discount": {
#                         "discount_sum": 140,
#                         "discount_percent": 50,
#                         "discount_type": "SUM",
#                         "coupon": null,
#                         "discount_price": 140,
#                     },
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
#                     "id": "745f2d7e-3e80-4ae1-906f-e7e6cd694bde",
#                     "parent_id": null,
#                     "sum": 140,
#                     "type": "ELECTRON",
#                     "parts": [
#                         {
#                             "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                             "part_sum": 140,
#                             "change": 0,
#                         }
#                     ],
#                     "app_payment": null,
#                     "merchant_info": {
#                         "number": "123",
#                         "english_name": "123",
#                         "category_code": "123",
#                     },
#                     "bank_info": {"name": "ПАО СБЕРБАНК"},
#                     "app_info": {"app_id": null, "name": "Банковская карта"},
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
#                     "receipt_number": 37,
#                     "document_number": 39,
#                     "session_number": 148,
#                     "receipt_date": "05122024",
#                     "receipt_time": "1129",
#                     "fn_reg_number": null,
#                     "fiscal_sign_doc_number": "1277173456",
#                     "fiscal_document_number": 30171,
#                     "fn_serial_number": "7382440700036332",
#                     "kkt_serial_number": "00307900652283",
#                     "kkt_reg_number": "0008200608019020",
#                     "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                     "check_sum": 140,
#                 }
#             ],
#             "sum": 280,
#             "result_sum": 140,
#             "customer_email": null,
#             "customer_phone": null,
#         },
#         "counterparties": null,
#         "created_at": "2024-12-05T04:29:53.847+0000",
#         "version": "V2",
#     },
# }
