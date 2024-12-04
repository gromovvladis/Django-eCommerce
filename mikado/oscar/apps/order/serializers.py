import logging
from django.conf import settings
from rest_framework import serializers
from decimal import Decimal as D
from oscar.core.loading import get_model
from django.utils.timezone import now

logger = logging.getLogger("oscar.customer")

User = get_model("user", "User")
Store = get_model("store", "Store")
Product = get_model('catalogue', 'Product')
StockRecord = get_model("store", "StockRecord")

Order = get_model("order", "Order")
OrderNote = get_model("order", "OrderNote")
OrderDiscount = get_model("order", "OrderDiscount")
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
        fields = ('id', 'number', 'store_id', 'created_at', 'extras', 'body')

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

        # Order creation
        user = None
        if customer_phone:
            user = User.objects.filter(username=customer_phone).first()

        order = Order.objects.create(
            number=(900000 + number),
            evotor_id=evotor_id,
            site="Эвотор",
            user=user,
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

        # Lines creation
        store = Store.objects.get(evotor_id=store_id)
        for position in positions:
            product, _ = Product.objects.get_or_create(evotor_id=position["product_id"], defaults={"name": "Не созданый продукт"})
            stockrecord = product.stockrecords.filter(store__evotor_id=store_id, is_public=True)[0]
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
            # Line prices
            LinePrice.objects.create(
                order=order,
                line=line,
                quantity=line.quantity,
                price=line.line_price,
                tax_code=line.tax_code,
            )

        # Payments creation
        for payment in payments:
            source_type, _ = SourceType.objects.get_or_create(name=payment["type"])
            source = Source.objects.create(
                order=order,
                source_type=source_type,
                amount_debited=D(payment["sum"]) - D(payment["parts"]["change"]),
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
            frequency_base = OrderDiscount.objects.filter(message="Скидка сотрудником").count()
            for i, discount in enumerate(discounts, start=1):
                OrderDiscount.objects.create(
                    order=order,
                    category=OrderDiscount.BASKET,
                    message="Скидка сотрудником",
                    voucher_code=discount.get("coupon"),
                    amount=discount.get("discount_sum", 0),
                    frequency=frequency_base + i,
                )

        return order
