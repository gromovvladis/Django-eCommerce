from core.loading import get_model
from rest_framework import serializers

Staff = get_model("user", "Staff")
Store = get_model("store", "Store")
StockRecord = get_model("store", "StockRecord")
StockRecordOperation = get_model("store", "StockRecordOperation")
StoreCashTransaction = get_model("store", "StoreCashTransaction")
StoreAddress = get_model("store", "StoreAddress")
Terminal = get_model("store", "Terminal")


class StoreAddressSerializer(serializers.ModelSerializer):
    address = serializers.CharField(source="line1")

    class Meta:
        model = StoreAddress
        fields = ["address"]


class StoreSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="evotor_id")
    name = serializers.CharField()
    address = serializers.CharField(write_only=True, required=False)
    updated_at = serializers.DateTimeField(write_only=True)

    class Meta:
        model = Store
        fields = ["id", "name", "address", "updated_at"]

    def create(self, validated_data):
        # Извлекаем адрес из данных, если передан
        validated_data.pop("updated_at", None)

        address_data = validated_data.pop("address", None)
        # Создаем объект партнера
        store = Store.objects.create(**validated_data)

        # Если адрес передан, сохраняем его как отдельную запись в StoreAddress
        if address_data:
            StoreAddress.objects.create(store=store, line1=address_data)

        return store

    def update(self, instance, validated_data):
        # Обновляем данные партнера
        instance.name = validated_data.get("name", instance.name)
        instance.save()

        # Обрабатываем адрес отдельно
        address_data = validated_data.get("address")
        if address_data:
            # Если адрес уже существует, обновляем его
            existing_address = StoreAddress.objects.filter(store=instance).first()
            if existing_address:
                existing_address.coords_long = None
                existing_address.coords_lat = None
                existing_address.line1 = address_data
                existing_address.save()
            else:
                # Создаем новый адрес, если его нет
                StoreAddress.objects.create(store=instance, line1=address_data)

        return instance


class StoresSerializer(serializers.ModelSerializer):
    items = StoreSerializer(many=True)

    class Meta:
        model = Store
        fields = ["items"]

    def create(self, validated_data):
        items_data = validated_data.get("items", [])
        return [StoreSerializer().create(item_data) for item_data in items_data]

    def update(self, instances, validated_data):
        items_data = validated_data.get("items", [])
        stores = []

        for item_data in items_data:
            try:
                store_instance = instances.get(
                    evotor_id=item_data["id"]
                )  # `instance` — это QuerySet
                store = StoreSerializer().update(store_instance, item_data)
            except Store.DoesNotExist:
                continue  # Пропускаем, если объект не найден

            stores.append(store)

        return stores


class TerminalSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="evotor_id")
    name = serializers.CharField()
    model = serializers.CharField(required=False)
    serial_number = serializers.CharField()
    imei = serializers.CharField(required=False)

    store_id = serializers.CharField(write_only=True)
    location = serializers.JSONField(write_only=True, required=False)
    updated_at = serializers.DateTimeField(write_only=True)

    class Meta:
        model = Terminal
        fields = [
            "id",
            "name",
            "model",
            "serial_number",
            "imei",
            "store_id",
            "location",
            "updated_at",
        ]

    def create(self, validated_data):

        validated_data.pop("updated_at", None)
        store_id = validated_data.pop("store_id")

        location = validated_data.pop("location", {})
        coords_long = location.get("lng", None)
        coords_lat = location.get("lat", None)

        terminal = Terminal.objects.create(
            coords_long=coords_long, coords_lat=coords_lat, **validated_data
        )

        store, created = Store.objects.get_or_create(evotor_id=store_id)
        store.terminals.add(terminal)

        return terminal

    def update(self, instance, validated_data):
        store_id = validated_data.pop("store_id")
        location = validated_data.pop("location", {})

        coords_long = location.get("lng")
        coords_lat = location.get("lat")

        # Обновляем терминал
        instance.coords_long = coords_long
        instance.coords_lat = coords_lat
        instance.model = validated_data.get("model", instance.model)
        instance.serial_number = validated_data.get(
            "serial_number", instance.serial_number
        )
        instance.imei = validated_data.get("imei", instance.imei)
        instance.name = validated_data.get("name", instance.name)

        instance.save()

        # Получаем или создаем партнера
        store, created = Store.objects.get_or_create(evotor_id=store_id)

        # Удаляем терминал у других партнеров
        other_stores = Store.objects.all()
        for other_store in other_stores:
            terminals_to_remove = other_store.terminals.filter(id=instance.id)
            if terminals_to_remove.exists():
                other_store.terminals.remove(*terminals_to_remove)  # Удаляем терминалы

        # Добавляем обновленный терминал к партнеру
        store.terminals.add(instance)

        return instance


class TerminalsSerializer(serializers.ModelSerializer):
    items = TerminalSerializer(many=True)

    class Meta:
        model = Terminal
        fields = ["items"]

    def create(self, validated_data):
        items_data = validated_data.get("items", [])
        return [TerminalSerializer().create(item_data) for item_data in items_data]

    def update(self, instances, validated_data):
        items_data = validated_data.get("items", [])
        terminals = []

        for item_data in items_data:
            try:
                terminal_instance = instances.get(
                    evotor_id=item_data["id"]
                )  # `instance` — это QuerySet
                terminal = TerminalSerializer().update(terminal_instance, item_data)
            except Terminal.DoesNotExist:
                continue  # Пропускаем, если объект не найден

            terminals.append(terminal)

        return terminals


class StoreCashTransactionSerializer(serializers.Serializer):
    id = serializers.CharField(source="evotor_id")
    type = serializers.CharField()
    store_id = serializers.CharField(write_only=True)
    body = serializers.DictField(write_only=True)

    class Meta:
        model = StoreCashTransaction
        fields = ("id", "store_id", "body")

    def create(self, validated_data):
        evotor_id = validated_data.get("evotor_id")
        type = validated_data.get("type")
        store_id = validated_data.get("store_id")
        body = validated_data.get("body")

        store = Store.objects.get(evotor_id=store_id)

        if type == "CASH_INCOME":
            type_trs = "Внесение наличных"
            description = f"Комментарий: {body.get('description', '-')}, Внес: {body.get('contributor')}"

        else:
            type_trs = "Изъятие наличных"
            description = f"Комментарий: {body.get('description', '-')}, Категория: {body.get('payment_category_name')}, Изъял: {body.get('receiver')}"

        store_transaction = StoreCashTransaction.objects.create(
            evotor_id=evotor_id,
            type=type_trs,
            description=description,
            store=store,
            sum=body.get("sum", 0),
        )

        return store_transaction

    def update(self, instance, validated_data):
        type = validated_data.get("type")
        store_id = validated_data.get("store_id")
        body = validated_data.get("body")

        store = Store.objects.get(evotor_id=store_id)

        if type == "CASH_INCOME":
            type_trs = "Внесение наличных"
            description = f"Комментарий: {body.get('description', '-')}, Внес: {body.get('contributor')}"

        else:
            type_trs = "Изъятие наличных"
            description = f"Комментарий: {body.get('description', '-')}, Категория: {body.get('payment_category_name')}, Изъял: {body.get('receiver')}"

        instance.update(
            type=type_trs,
            description=description,
            store=store,
            total=body.get("sum", 0),
        )

        return instance


class StockRecordOperationSerializer(serializers.ModelSerializer):
    store_id = serializers.CharField(write_only=True)
    type = serializers.CharField(write_only=True)
    close_user_id = serializers.CharField(write_only=True)
    body = serializers.DictField(write_only=True)

    class Meta:
        model = StockRecordOperation
        fields = [
            "store_id",
            "type",
            "close_user_id",
            "body",
        ]

    def validate(self, data):
        """
        Валидация данных в зависимости от типа операции.
        """
        operation_type = data.get("type")
        body = data.get("body", {})
        positions = body.get("positions", [])

        if not positions and not operation_type:
            raise serializers.ValidationError("Позиции не могут быть пустыми.")

        return data

    def create(self, validated_data):
        """
        Создание операций для каждой позиции.
        """
        body = validated_data.pop("body")
        positions = body.get("positions", [])
        store_id = validated_data.pop("store_id")
        raw_type = validated_data.pop("type")
        close_user_id = validated_data.pop("close_user_id", None)

        if raw_type == "ACCEPT":
            type = "Приемка"
        elif raw_type == "WRITE_OFF":
            type = "Списание"
        else:
            type = "Инвентаризация"

        if close_user_id:
            staff = Staff.objects.filter(evotor_id=close_user_id).first()
        else:
            staff = None
        operations = []

        for position in positions:
            stockrecord = StockRecord.objects.get(
                product__evotor_id=position["product_id"], store__evotor_id=store_id
            )
            operation = StockRecordOperation.objects.create(
                stockrecord=stockrecord,
                type=type,
                message=validated_data.get("message"),
                user=staff.user if staff else None,
                num=position["quantity"],
            )
            operations.append(operation)

        return operations
