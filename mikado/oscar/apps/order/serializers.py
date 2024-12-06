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

        positions = body.get("positions", [])
        discounts = body.get("doc_discounts", [])
        payments = body.get("payments", [])
        result_sum = body.get("result_sum", 0)
        customer_phone = body.get("customer_phone")

        user = (
            User.objects.filter(username=customer_phone).first()
            if customer_phone
            else None
        )

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
            ).first()

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

            position_discount = position.get("position_discount", None)
            if position_discount:
                order_discount = OrderDiscount(
                    order=order,
                    message="Скидка сотрудником позицию заказа",
                    amount=position_discount.get("discount_sum", 0),
                    voucher_code=position_discount.get("coupon") or "",
                )
                order_discount.save()
                line.discounts.create(
                    order_discount=order_discount,
                    amount=position_discount.get("discount_sum", 0),
                )

        for payment in payments:
            source_type, _ = SourceType.objects.get_or_create(name=payment["type"])
            amount_debited = sum(
                D(part["part_sum"]) - D(part["change"])
                for part in payment.get("parts", [])
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

        for discount in discounts:
            order_discount = OrderDiscount(
                order=order,
                message="Скидка сотрудником на весь заказ",
                amount=discount.get("discount_sum", 0),
                voucher_code=discount.get("coupon") or "",
            )
            order_discount.save()

        return order

    def update(self, instance, validated_data):
        return instance

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

