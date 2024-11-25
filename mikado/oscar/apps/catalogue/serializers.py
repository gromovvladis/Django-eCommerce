import logging
from rest_framework import serializers
from django.contrib.auth.models import Group
from oscar.apps.customer.models import GroupEvotor
from oscar.apps.search.search_indexes import ProductIndex
from decimal import Decimal as D
from oscar.core.loading import get_model
from haystack import connections

logger = logging.getLogger("oscar.customer")

User = get_model("user", "User")
Staff = get_model("user", "Staff")
Store = get_model("store", "Store")
Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
StockRecord = get_model("store", "StockRecord")
Category = get_model("catalogue", "Category")


class ProductSerializer(serializers.ModelSerializer):
    # товар
    id = serializers.CharField(source="evotor_id")
    name = serializers.CharField(source="title")
    article_number = serializers.CharField(source="upc", required=False, allow_blank=True)
    description = serializers.CharField(
        source="short_description", required=False, allow_blank=True
    )
    parent_id = serializers.CharField(required=False, allow_blank=True, write_only=True)

    # класс товара
    type = serializers.CharField(write_only=True, required=False)
    measure_name = serializers.CharField(write_only=True, required=False)

    # товарная запись
    code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    store_id = serializers.CharField(write_only=True, required=False)
    price = serializers.CharField(write_only=True, required=False)
    cost_price = serializers.CharField(write_only=True, required=False)
    quantity = serializers.CharField(write_only=True, required=False)
    tax = serializers.CharField(write_only=True, required=False)
    allow_to_sell = serializers.BooleanField(write_only=True, required=False)

    updated_at = serializers.DateTimeField(write_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "code",
            "article_number",
            "description",
            "parent_id",
            "type",
            "measure_name",
            "store_id",
            "price",
            "cost_price",
            "quantity",
            "tax",
            "allow_to_sell",
            "updated_at",
        ]

    def create(self, validated_data):
        # Извлечение данных из validated_data
        parent_id = validated_data.pop("parent_id", None)
        measure_name = validated_data.pop("measure_name", None)
        store_id = validated_data.pop("store_id", None)
        price = validated_data.pop("price", None)
        cost_price = validated_data.pop("cost_price", None)
        quantity = validated_data.pop("quantity", None)
        tax = validated_data.pop("tax", None)
        allow_to_sell = validated_data.pop("allow_to_sell", None)
        code = validated_data.pop("code", None)

        type = validated_data.pop("type", None)
        updated_at = validated_data.pop("updated_at", None)

        evotor_id = validated_data.get("evotor_id")

        # Инициализация переменных
        parent_product = category = None

        # Обработка родительского товара или категории
        if parent_id:
            parent_product = self._get_parent_product(parent_id)
            category = self._get_category(parent_id)

        # Создание типа товара
        product_class = self._get_or_create_product_class(measure_name, quantity)

        # Создание или извлечение товара
        product = self._get_or_create_product(evotor_id, validated_data, parent_product, product_class)

        # Добавление категории, если она не существует
        if category is None:
            category = self._get_or_create_category()

        # Добавление категории к товару
        self._add_category_to_product(product, category)

        # Обновление родительского товара и структуры, если необходимо
        if parent_product:
            self._update_parent_product(product, parent_product)

        # Сохранение товара
        self._save(product)

        # Создание или извлечение партнера
        store = self._get_or_create_store(store_id)

        # Обработка товарной записи
        if code:
            self._create_or_update_stock_record(product, store, code, price, cost_price, quantity, tax, allow_to_sell)

        return product

    def update(self, product, validated_data):
        # Извлечение данных из validated_data
        parent_id = validated_data.pop("parent_id", None)
        store_id = validated_data.pop("store_id", None)
        price = validated_data.pop("price", None)
        cost_price = validated_data.pop("cost_price", None)
        quantity = validated_data.pop("quantity", None)
        tax = validated_data.pop("tax", None)
        allow_to_sell = validated_data.pop("allow_to_sell", None)
        code = validated_data.pop("code", None)

        # Инициализация переменных
        parent_product = category = None

        # Обработка родительского товара или категории
        if parent_id:
            parent_product = self._get_parent_product(parent_id)
            category = self._get_category(parent_id)
        
        product.title = validated_data.get("title")
        product.upc = validated_data.get("upc")
        product.short_description = validated_data.get("short_description")

        # Добавление категории к товару
        if category:
            self._add_category_to_product(product, category)

        # Обновление родительского товара и структуры, если необходимо
        if parent_product:
            self._update_parent_product(product, parent_product)

        # Сохранение товара
        self._save(product)

        # Создание или извлечение партнера
        store = self._get_or_create_store(store_id)

        # Обработка товарной записи
        if code:
            self._create_or_update_stock_record(product, store, code, price, cost_price, quantity, tax, allow_to_sell)

        return product
    
    def _save(self, product):
        product.save()
        search_backend = connections['default'].get_backend()
        search_backend.update(ProductIndex(), [product])

    def _get_parent_product(self, parent_id):
        """Обработка родительского товара или категории"""
        try:
            parent_product = Product.objects.get(evotor_id=parent_id)
            parent_product.structure = Product.PARENT
            parent_product.save()
            return parent_product
        except Product.DoesNotExist:
            return None

    def _get_or_create_product_class(self, measure_name, quantity):
        """Создание или извлечение класса товара"""
        return ProductClass.objects.get_or_create(
            name="Тип товара Эвотор",
            defaults={
                "track_stock": bool(quantity),
                "requires_shipping": False,
                "measure_name": measure_name,
            }
        )[0]

    def _get_or_create_product(self, evotor_id, validated_data, parent_product, product_class):
        """Создание или извлечение товара"""
        return Product.objects.get_or_create(
            evotor_id=evotor_id,
            defaults={
                "structure": Product.STANDALONE if not parent_product else Product.CHILD,
                "product_class": product_class,
                "is_public": True,
                "parent": parent_product,
                **validated_data
            }
        )[0]
    
    def _get_category(self, parent_id=None):
        """Создание или извлечение категории"""
        try:
            return Category.objects.get(evotor_id=parent_id)
        except Category.DoesNotExist:
            return None

    def _get_or_create_category(self, parent_id=None):
        """Создание или извлечение категории"""
        return Category.objects.get_or_create(
            evotor_id=parent_id,
            defaults={
                "is_public": False,
                "depth": 1,
                "numchild": 0,
                "name": "Категория Эвотор" if not parent_id else "Категория",
            }
        )[0]

    def _add_category_to_product(self, product, category):
        """Добавление категории к товару"""
        product.categories.add(category)

    def _update_parent_product(self, product, parent_product):
        """Обновление родительского товара и структуры"""
        product.parent_product = parent_product
        product.structure = Product.CHILD

    def _get_or_create_store(self, store_id):
        """Создание или извлечение партнера"""
        return Store.objects.get_or_create(evotor_id=store_id)[0]

    def _create_or_update_stock_record(self, product, store, code, price, cost_price, quantity, tax, allow_to_sell):
        """Создание или обновление товарной записи"""
        stockrecord, created = StockRecord.objects.get_or_create(
            evotor_code=code,
            defaults={
                "product": product,
                "store": store,
                "price": D(price),
                "cost_price": D(cost_price),
                "is_public": allow_to_sell,
                "num_in_stock": int(quantity),
                "tax": tax,
            },
        )

        if created:
            stockrecord.save()
        else:
            stockrecord.price = D(price)
            stockrecord.cost_price = D(cost_price)
            stockrecord.is_public = allow_to_sell
            stockrecord.num_in_stock = int(quantity)
            stockrecord.tax = tax
            stockrecord.save()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        try:
            if instance.parent:
                representation["parent_id"] = instance.parent.evotor_id
            else:
                cat_id = instance.categories.first().evotor_id
                if cat_id:
                    representation["parent_id"] = cat_id
                 
            representation["measure_name"] = instance.get_product_class().measure_name

            store_id = self.context.get("store_id", None)
            
            stc = StockRecord.objects.filter(product=instance, store__evotor_id=store_id).first()

            if stc:
                representation["code"] = stc.evotor_code
                representation["price"] = stc.price
                representation["cost_price"] = stc.cost_price
                representation["quantity"] = stc.num_in_stock
                representation["tax"] = stc.tax
                representation["allow_to_sell"] = stc.is_public

        except Exception as e:
            logger.error(f"Ошибка определения товара: {e}")
            representation["measure_name"] = "шт"
            representation["tax"] = "NO_VAT"
            representation["allow_to_sell"] = False
            representation["price"] = 0
            representation["cost_price"] = 0
            representation["quantity"] = 0

        representation["type"] = "NORMAL"

        if not representation.get("id"):
            representation.pop("id", None)

        return representation


class ProductsSerializer(serializers.ModelSerializer):
    items = ProductSerializer(many=True)

    class Meta:
        model = Product
        fields = ["items"]

    def create(self, validated_data):    
        items_data = validated_data.get("items", [])
        store_id = self.context.get("store_id", None)
        return [ProductSerializer(context={"store_id": store_id}).create(item_data) for item_data in items_data]

    def update(self, instances, validated_data):
        items_data = validated_data.get('items', [])
        store_id = self.context.get("store_id", None)
        products = []

        for item_data in items_data:
            try:
                product_instance = instances.get(evotor_id=item_data['id'])  # `instance` — это QuerySet
                product = ProductSerializer(context={"store_id": store_id}).update(product_instance, item_data)
            except Product.DoesNotExist:
                continue  # Пропускаем, если объект не найден

            products.append(product)

        return products


class ProductGroupSerializer(serializers.ModelSerializer):
    # товар
    id = serializers.CharField(source="evotor_id")
    name = serializers.CharField(source="title")
    code = serializers.CharField(source="evotor_code", required=False, allow_blank=True)
    article_number = serializers.CharField(source="upc", required=False, allow_blank=True)
    description = serializers.CharField(
        source="middle_name", required=False, allow_blank=True
    )

    # класс товара
    type = serializers.CharField(write_only=True, required=False)
    measure_name = serializers.CharField(write_only=True, required=False)

    # товарная запись
    store_id = serializers.CharField(write_only=True, required=False)
    price = serializers.CharField(write_only=True, required=False)
    cost_price = serializers.CharField(write_only=True, required=False)
    quantity = serializers.CharField(write_only=True, required=False)
    tax = serializers.CharField(write_only=True, required=False)
    allow_to_sell = serializers.BooleanField(write_only=True, required=False)

    updated_at = serializers.DateTimeField(write_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "code",
            "article_number",
            "description",
            "type",
            "measure_name",
            "store_id",
            "price",
            "cost_price",
            "quantity",
            "tax",
            "allow_to_sell",
            "updated_at",
        ]

    def create(self, validated_data):
        # Извлекаем адрес из данных, если передан
        updated_at = validated_data.pop("updated_at", None)
        phone_data = validated_data.pop("phone", None)
        stores_data = validated_data.pop("stores", None)
        role_data = validated_data.pop("role", None)
        role_id_data = validated_data.pop("role_id", None)

        first_name = validated_data.get("first_name", "")

        # Получаем или создаем пользователя, проверяя на существование по username
        if phone_data:
            user, created = User.objects.get_or_create(
                username=phone_data,
                defaults={
                    "is_staff": True,
                    "name": first_name,
                },
            )
            # Если пользователь уже существовал, обновляем его данные, если они отличаются
            if not created:
                user.is_staff = True
                user.name = first_name
                user.save()

            if stores_data:
                stores = Store.objects.filter(evotor_id__in=stores_data)
                for store in stores:
                    store.users.add(user)

            staff, _ = Staff.objects.get_or_create(user=user)
        else:
            staff = Staff.objects.create(**validated_data)

        for attr, value in validated_data.items():
            setattr(staff, attr, value)

        if role_data:
            group, _ = Group.objects.get_or_create(name=role_data)
            group_evotor, _ = GroupEvotor.objects.get_or_create(group=group)
            group_evotor.evotor_id = role_id_data
            group_evotor.save()
            staff.role = group

        staff.save()

        return staff

    def update(self, instance, validated_data):
        # Извлекаем данные
        phone_data = validated_data.pop("phone", None)
        stores_data = validated_data.pop("stores", None)
        role_data = validated_data.pop("role", None)
        role_id_data = validated_data.pop("role_id", None)

        first_name = validated_data.get("first_name", "")

        # Обновляем данные пользователя
        if phone_data:
            user, created = User.objects.get_or_create(
                username=phone_data,
                defaults={
                    "is_staff": True,
                    "name": first_name,
                },
            )
            # Если пользователь уже существовал, обновляем его данные, если они отличаются
            if not created:
                user.is_staff = True
                user.name = first_name
                user.save()

            instance.user = user

        # Обновляем информацию о сотруднике
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.middle_name = validated_data.get("middle_name", instance.middle_name)

        # Обновляем привязку к партнёрам
        stores = Store.objects.filter(users=instance.user)
        for store in stores:
            store.users.remove(instance.user)

        # Добавляем новые привязки
        if stores_data and instance.user:
            new_stores = Store.objects.filter(evotor_id__in=stores_data)
            for new_store in new_stores:
                new_store.users.add(instance.user)

        # Обновляем роль
        if role_data:
            group, _ = Group.objects.get_or_create(name=role_data)
            group_evotor, _ = GroupEvotor.objects.get_or_create(group=group)
            group_evotor.evotor_id = role_id_data
            group_evotor.save()
            instance.role = group

        instance.save()

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        try:
            representation["stores"] = [
                store.evotor_id for store in instance.user.stores.all()
            ]
            representation["phone"] = str(instance.user.username)
            role = instance.role.evotor
            if role:
                representation["role_id"] = role.evotor_id
        except Exception as e:
            logger.error(f"Ошибка определения списка магазинов сотрудника: {e}")
            representation["stores"] = []
            representation["phone"] = ""
            representation["role_id"] = ""
        return representation


class ProductsGroupSerializer(serializers.ModelSerializer):
    items = ProductGroupSerializer(many=True)

    class Meta:
        model = Category
        model_product = Product
        fields = ["items"]
    
    def create(self, validated_data):    
        items_data = validated_data.get("items", [])
        store_id = self.context.get("store_id", None)
        return [ProductGroupSerializer(context={"store_id": store_id}).create(item_data) for item_data in items_data]

    def update(self, instances, validated_data):
        items_data = validated_data.get('items', [])
        store_id = self.context.get("store_id", None)
        product_groups = []

        for item_data in items_data:
            try:
                product_group_instance = instances.get(evotor_id=item_data['id'])  # `instance` — это QuerySet
                product_group = ProductGroupSerializer(context={"store_id": store_id}).update(product_group_instance, item_data)
            except Product.DoesNotExist:
                continue  # Пропускаем, если объект не найден

            product_groups.append(product_group)

        return product_groups
    