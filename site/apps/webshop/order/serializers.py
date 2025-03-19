from decimal import Decimal as D

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Coalesce, Greatest
from django.utils.timezone import now
from core.loading import get_model
from rest_framework import serializers

User = get_model("user", "User")
Store = get_model("store", "Store")
Product = get_model("catalogue", "Product")
Additional = get_model("catalogue", "Additional")
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


class OrderLineSerializer(serializers.Serializer):
    uuid = serializers.CharField(source="evotor_id")
    product_id = serializers.CharField()
    quantity = serializers.IntegerField()
    code = serializers.CharField(required=False)
    result_sum = serializers.DecimalField(
        source="line_price", max_digits=12, decimal_places=2
    )
    sum = serializers.DecimalField(
        source="line_price_before_discounts", max_digits=12, decimal_places=2
    )
    price = serializers.DecimalField(
        source="unit_price", max_digits=12, decimal_places=2
    )
    tax = serializers.DictField()
    position_discount = serializers.DictField(required=False)

    def create_line(self, validated_data, order, store):
        if validated_data.get("parent_id", None) != Additional.parent_id:
            product, stockrecord = self._get_product_and_stockrecord(
                store, validated_data
            )
            line = self._create_line(
                order,
                store,
                validated_data,
                product,
                stockrecord,
            )
            if stockrecord.can_track_allocations:
                stockrecord.num_in_stock = Greatest(
                    Coalesce(F("num_in_stock"), 0) - line.quantity, 0
                )
                stockrecord.save()

        else:
            line = self._create_line(order, store, validated_data)

        self._create_or_update_line_price(order, line)
        self._create_or_update_position_discount(
            order, line, validated_data.get("position_discount")
        )

        return line

    def update_line(self, instance, validated_data, order, store, type):
        line_status = (
            settings.FAIL_LINE_STATUS
            if type == "PAYBACK"
            else settings.SUCCESS_LINE_STATUS
        )
        old_quantity = instance.quantity
        if validated_data.get("parent_id", None) != Additional.parent_id:
            product, stockrecord = self._get_product_and_stockrecord(
                store, validated_data
            )
            line = self._update_line(
                instance,
                validated_data,
                line_status,
                product,
                stockrecord,
            )
            if stockrecord.can_track_allocations:
                new_quantity = (
                    -line.quantity
                    if type == "PAYBACK"
                    else (
                        line.quantity - old_quantity
                        if type == "CORRECTION"
                        else line.quantity
                    )
                )
                stockrecord.num_in_stock = Greatest(
                    Coalesce(F("num_in_stock"), 0) - new_quantity, 0
                )
                stockrecord.save()

        else:
            line = self._update_line(instance, validated_data, line_status)

        self._create_or_update_line_price(order, line)
        self._create_or_update_position_discount(
            order, line, validated_data.get("position_discount")
        )

        return line

    def _get_product_and_stockrecord(self, store, validated_data):
        product, _ = Product.objects.get_or_create(
            evotor_id=validated_data["product_id"],
            defaults={
                "name": validated_data["product_name"],
                "product_class": self._get_or_create_product_class(),
            },
        )

        stockrecord, _ = StockRecord.objects.get_or_create(
            product=product,
            store=store,
            defaults={
                "evotor_code": validated_data.get("code") or f"site-{product.id}",
                "price": D(validated_data["price"]),
            },
        )

        return product, stockrecord

    def _create_line(
        self, order, store, validated_data, product=None, stockrecord=None
    ):
        return Line.objects.create(
            order=order,
            store=store,
            store_name=store.name,
            stockrecord=stockrecord,
            product=product,
            name=product.get_name() if product else validated_data["product_name"],
            article=product.article if product else None,
            quantity=validated_data["quantity"],
            status=settings.SUCCESS_LINE_STATUS,
            evotor_id=validated_data["uuid"],
            line_price=validated_data["result_sum"],
            line_price_before_discounts=validated_data["sum"],
            unit_price=validated_data["price"],
            tax_code=validated_data["tax"]["type"],
        )

    def _update_line(
        self,
        line,
        validated_data,
        line_status,
        product=None,
        stockrecord=None,
    ):
        line.name = product.get_name() if product else validated_data["product_name"]
        line.article = product.article if product else None
        line.product = product
        line.stockrecord = stockrecord
        line.evotor_id = validated_data["uuid"]
        line.quantity = validated_data["quantity"]
        line.line_price = validated_data["result_sum"]
        line.line_price_before_discounts = validated_data["sum"]
        line.unit_price = validated_data["price"]
        line.tax_code = validated_data["tax"]["type"]
        line.status = line_status
        line.save()
        return line

    def _create_or_update_line_price(self, order, line):
        LinePrice.objects.update_or_create(
            order=order,
            line=line,
            defaults={
                "quantity": line.quantity,
                "price": line.line_price,
                "tax_code": line.tax_code,
            },
        )

    def _create_or_update_position_discount(self, order, line, position_discount):
        line.discounts.all().delete()
        if position_discount:
            discount_amount = position_discount.get("discount_sum", 0)
            voucher_code = position_discount.get("coupon") or ""
            order_discount, created = OrderDiscount.objects.get_or_create(
                order=order,
                voucher_code=voucher_code,
                defaults={
                    "message": "Скидка сотрудником на позицию заказа",
                    "category": OrderDiscount.ORDER,
                    "amount": discount_amount,
                    "frequency": 1,
                },
            )
            if not created:
                order_discount.amount += discount_amount
                order_discount.frequency += 1
                order_discount.save()

            line.discounts.create(
                order_discount=order_discount,
                amount=discount_amount,
            )

    def _get_or_create_product_class(self):
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
            "type": "NORMAL",
            "code": instance.stockrecord.evotor_code if instance.stockrecord else None,
            "commodity_id": instance.product.evotor_id if instance.product else None,
            "name": instance.name,
            "measureName": (
                instance.product.get_product_class().measure_name
                if instance.product
                else "шт"
            ),
            "quantity": instance.quantity,
            "tax": instance.tax_code,
            "price": instance.line_price_before_discounts,
            "priceWithDiscount": instance.line_price,
            "sub_positions": [
                {
                    "type": "NORMAL",
                    "commodity_id": additional.additional.evotor_id,
                    "name": additional.additional.name,
                    "measureName": "шт",
                    "quantity": additional.value,
                    "tax": additional.additional.tax,
                    "price": additional.additional.price,
                }
                for additional in instance.attributes.filter(additional__isnull=False)
            ],
        }


class OrderDiscountSerializer(serializers.Serializer):
    discount_sum = serializers.DecimalField(
        source="amount", max_digits=12, decimal_places=2
    )
    coupon = serializers.CharField(source="voucher_code", required=False)

    def create_discount(self, validated_data, order):
        OrderDiscount.objects.create(
            order=order,
            message="Скидка сотрудником на весь заказ",
            amount=validated_data["discount_sum"],
            voucher_code=validated_data.get("coupon") or "",
        )


class PaymentSerializer(serializers.Serializer):
    id = serializers.CharField(source="evotor_id")
    type = serializers.CharField(source="source_type")
    sum = serializers.DecimalField(source="amount", max_digits=12, decimal_places=2)
    app_info = serializers.DictField(source="reference")
    parts = serializers.ListField(child=serializers.DictField(), required=False)

    def create_payment(self, validated_data, order, type):
        source_type = self._get_source_type(validated_data)
        amount = self._get_transaction_amount(validated_data)

        source = Source.objects.create(
            order=order,
            source_type=source_type,
            amount_allocated=amount,
            reference=validated_data["type"],
        )

        is_refund = type == "PAYBACK"
        method = "new_refund" if is_refund else "new_payment"
        getattr(source, method)(
            amount=amount,
            reference="Эвотор",
            status="succeeded",
            paid=not is_refund,
            refundable=False,
            receipt=True,
            evotor_id=validated_data.get("id"),
        )

    def update_payment(self, validated_data, order, type):
        source_type = self._get_source_type(validated_data)
        transaction_amount = self._get_transaction_amount(validated_data)
        is_refund = type == "PAYBACK"
        is_correction = type == "CORRECTION"

        source, _ = Source.objects.get_or_create(
            order=order,
            source_type=source_type,
            defaults={
                "reference": validated_data["type"],
                "amount_allocated": transaction_amount,
            },
        )

        if is_refund:
            source.amount_allocated = source.amount_allocated - transaction_amount
        elif is_correction:
            source.amount_allocated = transaction_amount
        source.save()

        method = "update_refund" if is_refund else "update_payment"
        getattr(source, method)(
            amount=transaction_amount,
            reference="Эвотор",
            status="succeeded",
            paid=not is_refund,
            refundable=False,
            receipt=True,
            evotor_id=validated_data.get("id"),
        )

    def _get_source_type(self, validated_data):
        return SourceType.objects.get_or_create(
            name=validated_data["app_info"]["name"]
        )[0]

    def _get_transaction_amount(self, validated_data):
        return sum(
            D(part.get("part_sum", 0)) - D(part.get("change", 0))
            for part in validated_data.get("parts", [])
        )


class OrderSerializer(serializers.Serializer):
    id = serializers.CharField(source="evotor_id")
    type = serializers.CharField(write_only=True)
    number = serializers.IntegerField(write_only=True)
    store_id = serializers.CharField(write_only=True)
    created_at = serializers.DateTimeField(write_only=True)
    extras = serializers.DictField(write_only=True, required=False)
    body = serializers.DictField(write_only=True)

    def create(self, validated_data):
        with transaction.atomic():
            evotor_id = validated_data.get("evotor_id")
            store_id = validated_data.get("store_id")
            type = validated_data.get("type")
            number = validated_data.get("number")
            body = validated_data.get("body")

            store = Store.objects.get(evotor_id=store_id)
            order = self._create_order(evotor_id, number, type, body, store)
            self._create_extra_note(validated_data.get("extras", None), order)

            self._process_discounts(body.get("doc_discounts", []), order)
            self._process_positions(body.get("positions", []), order, store)
            self._process_payments(body.get("payments", []), order, type)

            return order

    def update(self, order, validated_data):
        with transaction.atomic():
            store_id = validated_data.get("store_id")
            type = validated_data.get("type")
            number = validated_data.get("number")
            body = validated_data.get("body")

            store = Store.objects.get(evotor_id=store_id)
            order = self._update_order(order, body, type)
            self._create_order_note(order, type, body, number)

            self._process_positions(body.get("positions", []), order, store, type)
            self._process_discounts(body.get("doc_discounts", []), order)
            self._process_payments(body.get("payments", []), order, type)

            return order

    def _create_extra_note(self, extras, order):
        if extras:
            OrderNote.objects.create(
                order=order,
                note_type=OrderNote.SYSTEM,
                message=str(extras),
            )

    def _process_positions(self, positions, order, store, type="SELL"):
        for position in positions:
            evotor_id = position.get("uuid")
            try:
                line = order.lines.get(evotor_id=evotor_id)
                OrderLineSerializer().update_line(line, position, order, store, type)
            except Line.DoesNotExist:
                OrderLineSerializer().create_line(position, order, store)

    def _process_discounts(self, discounts, order):
        OrderDiscount.objects.filter(order=order).delete()
        for discount in discounts:
            OrderDiscountSerializer().create_discount(discount, order)

    def _process_payments(self, payments, order, type):
        for payment in payments:
            if order.sources.filter(reference=payment["type"]).exists():
                PaymentSerializer().update_payment(payment, order, type)
            else:
                PaymentSerializer().create_payment(payment, order, type)

    def _create_order_note(self, order, type, body, number):
        message = f'{"Возврат" if type == "PAYBACK" else "Чек коррекции"}. Сообщение: {body.get("reason", f"Номер документа: {number}")}'
        OrderNote.objects.create(
            order=order,
            note_type=OrderNote.SYSTEM,
            message=message,
        )

    def _create_order(self, evotor_id, number, type, body, store):
        return Order.objects.create(
            number=f"E{100000 + number}",
            evotor_id=evotor_id,
            site="Эвотор",
            store=store,
            total=body.get("result_sum", 0),
            shipping_method="Самовывоз",
            status=(
                settings.FAIL_ORDER_STATUS
                if type == "PAYBACK"
                else settings.SUCCESS_ORDER_STATUS
            ),
            date_finish=now(),
            order_time=now(),
        )

    def _update_order(self, order, body, type):
        new_total = (
            order.total - body.get("result_sum", 0)
            if type == "PAYBACK"
            else body.get("result_sum", 0)
        )
        order.status = (
            settings.SUCCESS_ORDER_STATUS
            if new_total > 0
            else settings.FAIL_ORDER_STATUS
        )
        order.total = new_total
        order.date_finish = now()
        order.save()
        return order

    def to_representation(self, instance):
        paid = sum(
            src.amount_debited - src.amount_refunded for src in instance.sources.all()
        )

        representation = {
            "client_phone": str(instance.user.username) if instance.user else "",
            "client_email": instance.user.email if instance.user else "",
            "should_print_receipt": False,
            "editable": not paid,
            "payment_type": (
                instance.sources.last().reference if instance.sources.exists() else None
            ),
            "receiptDiscount": instance.total_discount,
            "extra": {
                "Номер заказа": instance.number,
                "Время заказа": instance.order_time,
                "Оплата": f"{paid}₽" if paid > 0 else "Нет",
                "Доставка": instance.shipping_method,
            },
            "positions": [
                OrderLineSerializer(line).data for line in instance.lines.all()
            ],
        }

        notes = instance.notes.values_list("note_type", "message")
        if notes.exists():
            representation["note"] = ", ".join(
                f"{note_type}: {message}" for note_type, message in notes
            )

        return representation
