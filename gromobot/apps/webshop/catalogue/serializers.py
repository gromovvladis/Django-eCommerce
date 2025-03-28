import logging
from decimal import Decimal as D

from apps.webshop.search.search_indexes import ProductIndex
from core.loading import get_model
from core.utils import slugify
from haystack import connections
from rest_framework import serializers

Store = get_model("store", "Store")
Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
StockRecord = get_model("store", "StockRecord")
Category = get_model("catalogue", "Category")
Attribute = get_model("catalogue", "Attribute")
AttributeOption = get_model("catalogue", "AttributeOption")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
ProductAttribute = get_model("catalogue", "ProductAttribute")
Additional = get_model("catalogue", "Additional")

logger = logging.getLogger("apps.webshop.customer")


class ProductSerializer(serializers.ModelSerializer):
    # Product
    id = serializers.CharField(source="evotor_id")
    name = serializers.CharField(required=False)
    article_number = serializers.CharField(
        source="article", required=False, allow_blank=True
    )
    description = serializers.CharField(
        source="short_description", required=False, allow_blank=True
    )
    parent_id = serializers.CharField(required=False, allow_blank=True, write_only=True)

    # Write-only fields

    # Product Class
    type = serializers.CharField(write_only=True, required=False)
    measure_name = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    # Stockrecord
    code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    store_id = serializers.CharField(write_only=True, required=False)
    price = serializers.CharField(write_only=True, required=False)
    cost_price = serializers.CharField(write_only=True, required=False)
    quantity = serializers.CharField(write_only=True, required=False)
    tax = serializers.CharField(write_only=True, required=False)
    allow_to_sell = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = Product
        fields = (
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
        )

    def create(self, validated_data):
        return self._process_product(validated_data)

    def update(self, product, validated_data):
        return self._process_product(validated_data, product)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        store_id = self.context.get("store_id")

        # Базовые поля
        rep.update(
            {
                "measure_name": "шт",
                "tax": "NO_VAT",
                "allow_to_sell": False,
                "price": 0,
                "cost_price": 0,
                "quantity": 0,
                "type": "NORMAL",
            }
        )

        try:
            # Основные данные товара
            product_class = instance.get_product_class()
            rep.update(
                {
                    "measure_name": product_class.measure_name,
                    "name": instance.get_name(),
                }
            )

            # Родительский товар
            if parent_id := instance.get_evotor_parent_id():
                rep["parent_id"] = parent_id

            # Складские данные
            if (
                stc := StockRecord.objects.filter(
                    product=instance, store__evotor_id=store_id
                )
                .select_related("store")
                .first()
            ):
                rep.update(
                    {
                        "code": stc.evotor_code,
                        "price": stc.price,
                        "cost_price": stc.cost_price,
                        "quantity": stc.num_in_stock,
                        "tax": stc.tax,
                        "allow_to_sell": stc.is_public,
                    }
                )

            # Атрибуты для дочерних товаров
            if instance.is_child:
                rep["attributes_choices"] = self._get_child_attributes(instance)

        except Exception as e:
            logger.error(f"Ошибка сериализации товара {instance.evotor_id}: {e}")

        # Очистка ID если пустой
        if not rep.get("id"):
            rep.pop("id", None)

        return rep

    def _process_product(self, data, product=None):
        """Общая логика для create/update"""
        parent_id = data.pop("parent_id", None)
        store_id = data.pop("store_id", None)

        # Подготовка данных
        stock_data = {
            "code": data.pop("code", None),
            "price": data.pop("price", None),
            "cost_price": data.pop("cost_price", None),
            "quantity": data.pop("quantity", None),
            "tax": data.pop("tax", None),
            "allow_to_sell": data.pop("allow_to_sell", None),
        }

        # Создание/обновление продукта
        product = self._get_or_update_product(data, parent_id, product)

        # Работа с магазином и складскими записями
        if store_id:
            store = Store.objects.get_or_create(evotor_id=store_id)[0]
            self._update_stock_record(product, store, **stock_data)

        return product

    def _get_or_update_product(self, data, parent_id=None, product=None):
        """Логика работы с продуктом"""
        if product:  # Режим обновления
            product.name = data.get("name", product.name)
            product.short_description = data.get(
                "short_description", product.short_description
            )
            if "article" in data:
                self._update_article(product, data["article"])
        else:  # Режим создания
            product = Product.objects.create(
                structure=Product.CHILD if parent_id else Product.STANDALONE,
                product_class=self._get_product_class(data.pop("measure_name", None)),
                parent=self._get_parent_product(parent_id) if parent_id else None,
                is_public=True,
                **data,
            )

        if parent_id:
            category = Category.objects.get_or_create(
                evotor_id=parent_id, defaults={"name": f"Категория {parent_id}"}
            )[0]
            product.categories.add(category)

        product.save()
        self._update_search_index(product)
        return product

    def _update_stock_record(self, product, store, **kwargs):
        """Обновление складской записи"""
        stock, created = StockRecord.objects.update_or_create(
            product=product,
            store=store,
            defaults={
                "evotor_code": kwargs.get("code") or f"site-{product.id}",
                "price": D(kwargs.get("price", 0)),
                "cost_price": D(kwargs.get("cost_price", 0)),
                "is_public": kwargs.get("allow_to_sell", False),
                "num_in_stock": int(kwargs.get("quantity", 0)),
                "tax": kwargs.get("tax"),
            },
        )
        return stock

    def _get_product_class(self, measure_name):
        return ProductClass.objects.get_or_create(
            name="Тип товара Эвотор",
            defaults={
                "track_stock": True,
                "requires_shipping": False,
                "measure_name": measure_name or "шт",
            },
        )[0]

    def _get_parent_product(self, parent_id):
        try:
            parent = Product.objects.get(evotor_id=parent_id)
            parent.structure = Product.PARENT
            parent.save()
            return parent
        except Product.DoesNotExist:
            return None

    def _update_article(self, product, article):
        """Генерация уникального артикула"""
        product.article = article
        for i in range(1, 100):
            if (
                not Product.objects.filter(article=product.article)
                .exclude(id=product.id)
                .exists()
            ):
                break
            product.article = f"{article}-{i}"
        return product.article

    def _update_search_index(self, product):
        search_backend = connections["default"].get_backend()
        search_backend.update(ProductIndex(), [product])

    def _get_child_attributes(self, instance):
        """Получение атрибутов для дочерних товаров"""
        return {
            av.attribute.option_group.evotor_id: v.evotor_id
            for av in instance.attribute_values.select_related(
                "attribute__option_group", "value"
            )
            if (v := av.value.first())
            and av.attribute.option_group
            and av.attribute.option_group.evotor_id
            and v.evotor_id
        }


class ProductsSerializer(serializers.Serializer):
    items = ProductSerializer(many=True)


class AttributeOptionSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


class AttributeOptionGroupSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    choices = AttributeOptionSerializer(many=True)


class ProductGroupSerializer(serializers.ModelSerializer):
    # Category / Parent product
    id = serializers.CharField(source="evotor_id")
    name = serializers.CharField()
    parent_id = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # Parent product atributes
    attributes = AttributeOptionGroupSerializer(
        many=True, write_only=True, required=False
    )

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "parent_id",
            "attributes",
        )

    def create(self, validated_data):
        attributes = validated_data.pop("attributes", [])
        parent_id = validated_data.pop("parent_id", None)

        if attributes:
            instance, _ = Product.objects.update_or_create(
                evotor_id=validated_data["id"],
                defaults={
                    "structure": Product.PARENT,
                    "product_class": self._get_product_class(),
                    "is_public": True,
                    **validated_data,
                },
            )
            instance.categories.add(self._create_or_update_category(parent_id))
            self._create_or_update_attributes(instance, attributes)
        else:
            instance = self._create_or_update_category(
                validated_data["id"], validated_data.get("name")
            )
            if parent_id:
                parent = self._create_or_update_category(parent_id)
                instance.move(parent, pos="first-child")

        return instance

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        attributes = validated_data.pop("attributes", [])
        parent_id = validated_data.pop("parent_id", None)
        
        if attributes:
            instance.structure = Product.PARENT
            instance.categories.add(self._create_or_update_category(parent_id))
            self._create_or_update_attributes(instance, attributes)
        elif parent_id:
            parent = self._create_or_update_category(parent_id)
            if parent and instance.get_parent() != parent:
                instance.move(parent, pos="first-child")
                instance.refresh_from_db()

        instance.save()
        return instance

    def to_representation(self, instance):
        if isinstance(instance, Product):
            self.Meta.model = Product
            representation = super().to_representation(instance)
            parent = instance.categories.first()
            if parent and parent.evotor_id:
                representation["parent_id"] = parent.evotor_id
            attribute_values = instance.attribute_values.filter(is_variant=True)
            representation["attributes"] = [
                {
                    "id": attribute_value.attribute.option_group.evotor_id,
                    "name": attribute_value.attribute.option_group.name,
                    "choices": [
                        {"id": choice.evotor_id, "name": choice.option}
                        for choice in attribute_value.value.all()
                        if choice.evotor_id
                    ],
                }
                for attribute_value in attribute_values
                if attribute_value.attribute.option_group
                and attribute_value.attribute.option_group.evotor_id
            ]
        else:
            self.Meta.model = Category
            representation = super().to_representation(instance)
            parent = instance.get_parent()
            if parent and parent.evotor_id:
                representation["parent_id"] = parent.evotor_id

        if not representation.get("id"):
            representation.pop("id", None)

        return representation

    def _create_or_update_category(self, evotor_id, name=None):
        """Создание или извлечение категории"""
        try:
            return Category.objects.get(
                evotor_id=evotor_id,
            )
        except Category.DoesNotExist:
            name = name or f"Категория {evotor_id}"
            base_name = name
            counter = 1

            # Проверяем уникальность имени сразу и формируем его при необходимости
            while Category.objects.filter(name=name).exists():
                name = f"{base_name}-{counter}"
                counter += 1

            return Category.add_root(name=name, evotor_id=evotor_id)

    def _create_or_update_attributes(self, instance, attributes):
        for attr in attributes:
            group, _ = AttributeOptionGroup.objects.update_or_create(
                evotor_id=attr["id"], defaults={"name": attr["name"]}
            )
            choices = [
                AttributeOption.objects.update_or_create(
                    evotor_id=choice["id"],
                    defaults={"option": choice["name"], "group": group},
                )[0]
                for choice in attr.get("choices", [])
            ]
            attr_obj, _ = Attribute.objects.update_or_create(
                name=attr["name"],
                defaults={
                    "type": "multi_option",
                    "option_group": group,
                    "code": slugify(attr["name"]),
                },
            )
            prd_attr, _ = ProductAttribute.objects.update_or_create(
                product=instance, attribute=attr_obj, defaults={"is_variant": True}
            )
            prd_attr.value_multi_option.set(choices)

    def _get_product_class(self):
        return ProductClass.objects.get_or_create(
            name="Тип товара Эвотор",
            defaults={
                "track_stock": True,
                "requires_shipping": False,
                "measure_name": "шт",
            },
        )[0]


class ProductGroupsSerializer(serializers.Serializer):
    items = ProductGroupSerializer(many=True)


class AdditionalSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="evotor_id")
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    article_number = serializers.CharField(
        source="article", required=False, allow_blank=True
    )
    parent_id = serializers.CharField(required=False, allow_blank=True, write_only=True)

    price = serializers.CharField(write_only=True, required=False)
    cost_price = serializers.CharField(write_only=True, required=False)
    store_id = serializers.CharField(write_only=True, required=False)
    allow_to_sell = serializers.BooleanField(
        source="is_public", write_only=True, required=False
    )
    tax = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "description",
            "article_number",
            "parent_id",
            "price",
            "cost_price",
            "store_id",
            "allow_to_sell",
            "tax",
        )

    def create(self, validated_data):
        # Извлечение данных из validated_data
        store_id = validated_data.pop("store_id", None)

        additional, created = Additional.objects.get_or_create(
            evotor_id=validated_data["evotor_id"],
            defaults={**validated_data},
        )

        # Если объект уже существует, обновляем данные
        if not created:
            for field, value in validated_data.items():
                setattr(additional, field, value)

        if store_id:
            additional.stores.set(Store.objects.filter(evotor_id=store_id))

        additional.save()
        return additional

    def update(self, additional, validated_data):
        store_id = validated_data.pop("store_id", None)

        # Обновляем поля объекта
        for field, value in validated_data.items():
            setattr(additional, field, value)

        # Обновляем магазины
        if store_id:
            additional.stores.set(Store.objects.filter(evotor_id=store_id))

        additional.save()
        return additional

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Обновляем поля в представлении
        representation.update(
            {
                "tax": instance.tax,
                "parent_id": instance.parent_id,
                "allow_to_sell": instance.is_public,
                "article_number": instance.article,
                "price": instance.price,
                "cost_price": instance.cost_price,
                "measure_name": "шт",
                "type": "NORMAL",
            }
        )

        if not representation.get("id"):
            representation.pop("id", None)

        return representation


class AdditionalsSerializer(serializers.Serializer):
    items = AdditionalSerializer(many=True)
