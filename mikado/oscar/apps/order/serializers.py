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


class LineSerializer(serializers.Serializer):
    id = serializers.CharField(source="article")
    product_id = serializers.CharField()
    code = serializers.CharField(source="evotor_code")
    quantity = serializers.IntegerField()
    result_sum = serializers.DecimalField(source="line_price", max_digits=12, decimal_places=2)
    sum = serializers.DecimalField(source="line_price_before_discounts", max_digits=12, decimal_places=2)
    price = serializers.DecimalField(source="unit_price", max_digits=12, decimal_places=2)
    tax = serializers.DictField()
    position_discount = serializers.DictField(required=False)

    class Meta:
        model = Line
        fields = ( "id", "product_id", "code", "quantity", "result_sum", "sum", "price", "tax", "position_discount")

    def create(self, validated_data, order, store):
        product, _ = Product.objects.get_or_create(
            evotor_id=validated_data["product_id"],
            defaults={
                "name": "Не созданый продукт",
                "product_class": self._get_or_create_product_class(),
            },
        )
        stockrecord = product.stockrecords.filter(
            store__evotor_id=store.evotor_id, is_public=True
        ).first()
        line = Line.objects.create(
            order=order,
            store=store,
            name=product.get_name(),
            store_name=store.name,
            evotor_code=validated_data["code"],
            product=product,
            stockrecord=stockrecord,
            quantity=validated_data["quantity"],
            article=validated_data["id"],
            line_price=validated_data["result_sum"],
            line_price_before_discounts=validated_data["sum"],
            unit_price=validated_data["price"],
            tax_code=validated_data["tax"]["type"],
        )
        LinePrice.objects.create(
            order=order,
            line=line,
            quantity=line.quantity,
            price=line.line_price,
            tax_code=line.tax_code,
        )

        position_discount = validated_data.get("position_discount", None)
        if position_discount:
            discount_amount = position_discount.get("discount_sum", 0)
            order_discount = OrderDiscount.objects.filter(order=order).first()
            if not order_discount:
                order_discount = OrderDiscount.objects.create(
                    order=order,
                    message="Скидка сотрудником позицию заказа",
                    amount=discount_amount,
                    frequency=1,
                    voucher_code=position_discount.get("coupon") or "",
                )
            else:
                order_discount.amount += discount_amount
                order_discount.frequency += 1
                order_discount.save()

            line.discounts.create(
                order_discount=order_discount,
                amount=discount_amount,
            )

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

    def to_representation(self, instance):
        return {
            # "settlement_method_type": "FULL",
            "type": "NORMAL",
            "code": instance.evotor_code,
            "commodity_id": instance.product.evotor_id,
            "name": instance.get_evotor_name(),
            "measureName": instance.product.get_product_class().measure_name,
            "quantity": instance.quantity,
            "tax": instance.tax_code,
            "price": instance.line_price_before_discounts,
            "priceWithDiscount": instance.line_price,
        }
    

class OrderDiscountSerializer(serializers.Serializer):
    discount_sum = serializers.DecimalField(source="amount", max_digits=12, decimal_places=2)
    coupon = serializers.CharField(source="voucher_code", required=False)

    class Meta:
        model = OrderDiscount
        fields = ("discount_sum", "coupon")

    def create(self, validated_data, order):
        OrderDiscount.objects.create(
            order=order,
            message="Скидка сотрудником на весь заказ",
            amount=validated_data["discount_sum"],
            voucher_code=validated_data.get("coupon") or "",
        )


class PaymentSerializer(serializers.Serializer):
    id = serializers.CharField(source="code")
    type = serializers.CharField(source="source_type")
    sum = serializers.DecimalField(source="amount", max_digits=12, decimal_places=2)
    app_info = serializers.DictField(source="reference")
    parts = serializers.ListField(child=serializers.DictField(), required=False)

    class Meta:
        model = Source
        fields = ("id", "type", "sum", "app_info", "parts")

    def create(self, validated_data, order):
        source_type, _ = SourceType.objects.get_or_create(name=validated_data["app_info"]["name"])
        amount_debited = sum(
            D(part["part_sum"]) - D(part["change"])
            for part in validated_data.get("parts", [])
        )
        source = Source.objects.create(
            order=order,
            source_type=source_type,
            amount_debited=amount_debited,
            reference=validated_data["type"],
            refundable=False,
            paid=True,
        )
        Transaction.objects.create(
            source=source,
            txn_type="Payment",
            amount=D(validated_data["sum"]),
            reference="Эвотор",
            status="succeeded",
            paid=True,
            refundable=False,
            code=validated_data["id"],
            receipt=True,
        )


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

        store = Store.objects.get(evotor_id=store_id)
        order = Order.objects.create(
            number=(900000 + number),
            evotor_id=evotor_id,
            site="Эвотор",
            store=store,
            total=body.get("result_sum", 0),
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

        positions = body.get("positions", [])
        for position in positions:
            LineSerializer().create(position, order, store)

        discounts = body.get("doc_discounts", [])
        for discount in discounts:
            OrderDiscountSerializer().create(discount, order)

        payments = body.get("payments", [])
        for payment in payments:
            PaymentSerializer().create(payment, order)

        return order

    def to_representation(self, instance):
        representation = {
            "client_phone": instance.user.username if instance.user else "",
            "client_email": instance.user.email if instance.user else "",
            "should_print_receipt": False,
            "editable": True,
            "payment_type": instance.sources.last().reference if instance.sources.exists() else None,
            "receiptDiscount": instance.total_discount,
            "extra": {
                "Номер заказа": instance.number,
                "Время заказа": instance.order_time,
                "Оплата": "Да" if instance.sources.filter(paid=True, refundable=False).exists() else "Нет",
                "Доставка": instance.shipping_method,
                },
            "positions": [LineSerializer(line).data for line in instance.lines.all()],
        }

        notes = instance.notes.values_list("note_type", "message")
        if notes.exists():
            representation["note"] = ", ".join(f"{note_type}: {message}" for note_type, message in notes)

        return representation
