import logging
from rest_framework import serializers
# from oscar.apps.payment.models import Receipt, ReceiptExtra
from oscar.core.loading import get_model

logger = logging.getLogger("oscar.customer")

Store = get_model("store", "Store")
Product = get_model("catalogue", "Product")
Source = get_model("payment", "Source")
SourceType = get_model("payment", "SourceType")
# ReceiptExtra = get_model("payment", "ReceiptExtra")
# Receipt = get_model("payment", "Receipt")


# class ReceiptExtraSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ReceiptExtra
#         fields = ["field_name", "field_value"]


# class ProductSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Product
#         fields = ["name", "price", "quantity"]  # Используйте нужные поля Product


# class ReceiptSerializer(serializers.ModelSerializer):
#     evotor_id = serializers.CharField(source="id")  # Переносим id в evotor_id
#     device_id = serializers.CharField()
#     store = serializers.PrimaryKeyRelatedField(queryset=Store.objects.all())
#     operation_type = serializers.ChoiceField(
#         choices=Receipt.RECEIPT_CHOICES, source="type"
#     )
#     shift_id = serializers.CharField()
#     employee_id = serializers.CharField()
#     info_check = serializers.BooleanField()
#     egais = serializers.BooleanField()
#     total_tax = serializers.DecimalField(max_digits=10, decimal_places=2)
#     total_discount = serializers.DecimalField(max_digits=10, decimal_places=2)
#     total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
#     extras = ReceiptExtraSerializer(many=True)
#     items = ProductSerializer(many=True)

#     # Получаем Source по SourceType
#     source = serializers.SerializerMethodField()

#     def get_source(self, obj):
#         payment_source_name = self.context["request"].data.get("paymentSource")
#         try:
#             source_type = SourceType.objects.get_or_create(code=payment_source_name)
#             source = Source.objects.filter(source_type=source_type).first()
#             return source.id if source else None
#         except Exception as e:
#             raise serializers.ValidationError(f"Ошибка {e}")

#     class Meta:
#         model = Receipt
#         fields = [
#             "evotor_id",
#             "device_id",
#             "store",
#             "operation_type",
#             "shift_id",
#             "employee_id",
#             "info_check",
#             "egais",
#             "total_tax",
#             "total_discount",
#             "total_amount",
#             "extras",
#             "items",
#             "source",
#         ]

#     def create(self, validated_data):
#         # Извлечение и удаление дополнительных данных
#         extras_data = validated_data.pop("extras", [])
#         items_data = validated_data.pop("items", [])

#         # Создание Receipt
#         receipt = Receipt.objects.create(**validated_data)

#         # Создание связанных объектов extras
#         for extra_data in extras_data:
#             ReceiptExtra.objects.create(receipt=receipt, **extra_data)

#         # Создание связанных объектов items
#         for item_data in items_data:
#             Product.objects.create(receipt=receipt, **item_data)

#         return receipt
    

# "method": "PUT",
# "path": "/crm/api/docs/",
# "data": {
#     "type": "SELL",
#     "id": "f5ebe0f4-1274-432b-811e-d847082dbf25",
#     "extras": {},
#     "number": 24901,
#     "close_date": "2024-11-06T03:58:24.000+0000",
#     "time_zone_offset": 25200000,
#     "session_id": "c6311fdb-39a0-4fbc-b886-dcae52782567",
#     "session_number": 120,
#     "close_user_id": "20240713-4403-40BB-80DA-F84959820434",
#     "device_id": "20240713-6F49-40AC-803B-E020F9D50BEF",
#     "store_id": "20240713-774A-4038-8037-E66BF3AA7552",
#     "user_id": "01-000000010409029",
#     "body": {
#         "positions": [
#             {
#                 "product_id": "2a0f4d45-6dbd-4d96-95dd-d80c4a824656",
#                 "quantity": 1,
#                 "initial_quantity": -4154,
#                 "quantity_in_package": null,
#                 "bar_code": null,
#                 "product_type": "NORMAL",
#                 "mark": null,
#                 "mark_data": null,
#                 "alcohol_by_volume": 0,
#                 "alcohol_product_kind_code": 0,
#                 "tare_volume": 0,
#                 "code": "8",
#                 "product_name": "Кофе 0,4",
#                 "measure_name": "шт",
#                 "id": 188298,
#                 "uuid": "841056e1-3e4d-4ae1-92b0-7d52cd3fb1c9",
#                 "extra_keys": [],
#                 "sub_positions": [],
#                 "measure_precision": 0,
#                 "price": 310,
#                 "cost_price": 0,
#                 "result_price": 155,
#                 "sum": 310,
#                 "tax": {"type": "NO_VAT", "sum": 0, "result_sum": 0},
#                 "result_sum": 155,
#                 "position_discount": null,
#                 "doc_distributed_discount": {
#                     "discount_sum": 155,
#                     "discount_percent": 50,
#                     "discount_type": "SUM",
#                     "coupon": null,
#                     "discount_price": null,
#                 },
#                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                 "splitted_positions": null,
#                 "attributes_choices": null,
#                 "settlement_method": {"type": "CHECKOUT_FULL", "amount": null},
#                 "agent_requisites": null,
#             }
#         ],
#         "doc_discounts": [
#             {
#                 "discount_sum": 155,
#                 "discount_percent": 50,
#                 "discount_type": "SUM",
#                 "coupon": null,
#             }
#         ],
#         "payments": [
#             {
#                 "id": "8ca4b4a3-405e-45ac-a768-61e32b9a264e",
#                 "parent_id": null,
#                 "sum": 155,
#                 "type": "ELECTRON",
#                 "parts": [
#                     {
#                         "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                         "part_sum": 155,
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
#                 "receipt_number": 3058,
#                 "document_number": 3270,
#                 "session_number": 119,
#                 "receipt_date": "06112024",
#                 "receipt_time": "1058",
#                 "fn_reg_number": null,
#                 "fiscal_sign_doc_number": "1632958513",
#                 "fiscal_document_number": 24444,
#                 "fn_serial_number": "7382440700036332",
#                 "kkt_serial_number": "00307900652283",
#                 "kkt_reg_number": "0008200608019020",
#                 "print_group_id": "46dd89f0-3a54-470a-a166-ad01fa34b86a",
#                 "check_sum": 155,
#             }
#         ],
#         "sum": 310,
#         "result_sum": 155,
#         "customer_email": null,
#         "customer_phone": null,
#     },
#     "counterparties": null,
#     "created_at": "2024-11-06T03:59:49.821+0000",
#     "version": "V2",
# },
