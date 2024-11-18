import logging
from rest_framework import serializers
from django.contrib.auth.models import Group
from oscar.apps.customer.models import GroupEvotor
from oscar.core.loading import get_model

logger = logging.getLogger("oscar.customer")

User = get_model("user", "User")
Staff = get_model("user", "Staff")
Partner = get_model("partner", "Partner")
Product = get_model('catalogue', 'Product')
Category = get_model("catalogue", "Category")

# {
#     # "type": "NORMAL", +
#     # "name": "По-венский 0,3", +
#     "code": "24",
#     # "price": 300, +
#     # "cost_price": 0, +
#     # "quantity": 0, +
#     # "measure_name": "шт", +
#     # "tax": "NO_VAT", +
#     # "allow_to_sell": True, +
#     # "description": "", +
#     "article_number": "",
#     "classification_code": "",
#     "quantity_in_package": 0,
#     # "id": "01028fa4-fa96-41ba-945a-41fad6a338da", +
#     # "store_id": "20240713-774A-4038-8037-E66BF3AA7552", +
#     "user_id": "01-000000010409029",
#     "created_at": "2024-07-13T06:31:37.360+0000",
#     # "updated_at": "2024-09-30T04:23:30.939+0000", +
#     "barcodes": [],
# }


class ProductSerializer(serializers.ModelSerializer):
    # продукт
    id = serializers.CharField(source="evotor_id")
    name = serializers.CharField(source="title")
    code = serializers.CharField(source="evotor_code", required=False, allow_blank=True)
    article_number = serializers.CharField(source="upc", required=False, allow_blank=True)
    description = serializers.CharField(
        source="middle_name", required=False, allow_blank=True
    )

    # класс продукта
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
        model = Product
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
        partners_data = validated_data.pop("stores", None)
        role_data = validated_data.pop("role", None)
        role_id_data = validated_data.pop("role_id", None)

        # Получаем или создаем пользователя, проверяя на существование по username
        if phone_data:
            user, created = User.objects.get_or_create(
                username=phone_data,
                defaults={
                    "is_staff": True,
                    "name": validated_data.get("first_name", ""),
                },
            )
            # Если пользователь уже существовал, обновляем его данные, если они отличаются
            if not created:
                user.is_staff = True
                user.name = validated_data.get("first_name", "")
                user.save()

            if partners_data:
                partners = Partner.objects.filter(evotor_id__in=partners_data)
                for partner in partners:
                    partner.users.add(user)

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
        partners_data = validated_data.pop("stores", None)
        role_data = validated_data.pop("role", None)
        role_id_data = validated_data.pop("role_id", None)

        # Обновляем данные пользователя
        if phone_data:
            user, created = User.objects.get_or_create(
                username=phone_data,
                defaults={
                    "is_staff": True,
                    "name": validated_data.get("first_name", ""),
                },
            )
            # Если пользователь уже существовал, обновляем его данные, если они отличаются
            if not created:
                user.is_staff = True
                user.name = validated_data.get("first_name", "")
                user.save()

            instance.user = user

        # Обновляем информацию о сотруднике
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.middle_name = validated_data.get("middle_name", instance.middle_name)

        # Обновляем привязку к партнёрам
        partners = Partner.objects.filter(users=instance.user)
        for partner in partners:
            partner.users.remove(instance.user)

        # Добавляем новые привязки
        if partners_data and instance.user:
            new_partners = Partner.objects.filter(evotor_id__in=partners_data)
            for new_partner in new_partners:
                new_partner.users.add(instance.user)

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
                partner.evotor_id for partner in instance.user.partners.all()
            ]
            representation["phone"] = str(instance.user.username)
            role = instance.role.evotor
            if role:
                representation["role_id"] = role.evotor_id
        except Exception as e:
            logger.error("Ошибка определения списка магазинов сотрудника", e)
            representation["stores"] = []
            representation["phone"] = ""
            representation["role_id"] = ""
        return representation


class ProductsSerializer(serializers.ModelSerializer):
    items = ProductSerializer(many=True)

    class Meta:
        model = Staff
        fields = ["items"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        staffs = []

        for item_data in items_data:
            staff = ProductSerializer().create(item_data)
            staffs.append(staff)

        return staffs

    def update(self, validated_data):
        items_data = validated_data.pop("items")
        staffs = []

        for item_data in items_data:
            staff = ProductSerializer().update(item_data)
            staffs.append(staff)

        return staffs


class GroupSerializer(serializers.ModelSerializer):
    # продукт
    id = serializers.CharField(source="evotor_id")
    name = serializers.CharField(source="title")
    code = serializers.CharField(source="evotor_code", required=False, allow_blank=True)
    article_number = serializers.CharField(source="upc", required=False, allow_blank=True)
    description = serializers.CharField(
        source="middle_name", required=False, allow_blank=True
    )

    # класс продукта
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
        partners_data = validated_data.pop("stores", None)
        role_data = validated_data.pop("role", None)
        role_id_data = validated_data.pop("role_id", None)

        # Получаем или создаем пользователя, проверяя на существование по username
        if phone_data:
            user, created = User.objects.get_or_create(
                username=phone_data,
                defaults={
                    "is_staff": True,
                    "name": validated_data.get("first_name", ""),
                },
            )
            # Если пользователь уже существовал, обновляем его данные, если они отличаются
            if not created:
                user.is_staff = True
                user.name = validated_data.get("first_name", "")
                user.save()

            if partners_data:
                partners = Partner.objects.filter(evotor_id__in=partners_data)
                for partner in partners:
                    partner.users.add(user)

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
        partners_data = validated_data.pop("stores", None)
        role_data = validated_data.pop("role", None)
        role_id_data = validated_data.pop("role_id", None)

        # Обновляем данные пользователя
        if phone_data:
            user, created = User.objects.get_or_create(
                username=phone_data,
                defaults={
                    "is_staff": True,
                    "name": validated_data.get("first_name", ""),
                },
            )
            # Если пользователь уже существовал, обновляем его данные, если они отличаются
            if not created:
                user.is_staff = True
                user.name = validated_data.get("first_name", "")
                user.save()

            instance.user = user

        # Обновляем информацию о сотруднике
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.middle_name = validated_data.get("middle_name", instance.middle_name)

        # Обновляем привязку к партнёрам
        partners = Partner.objects.filter(users=instance.user)
        for partner in partners:
            partner.users.remove(instance.user)

        # Добавляем новые привязки
        if partners_data and instance.user:
            new_partners = Partner.objects.filter(evotor_id__in=partners_data)
            for new_partner in new_partners:
                new_partner.users.add(instance.user)

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
                partner.evotor_id for partner in instance.user.partners.all()
            ]
            representation["phone"] = str(instance.user.username)
            role = instance.role.evotor
            if role:
                representation["role_id"] = role.evotor_id
        except Exception as e:
            logger.error("Ошибка определения списка магазинов сотрудника", e)
            representation["stores"] = []
            representation["phone"] = ""
            representation["role_id"] = ""
        return representation


class GroupsSerializer(serializers.ModelSerializer):
    items = GroupSerializer(many=True)

    class Meta:
        model = Staff
        fields = ["items"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        staffs = []

        for item_data in items_data:
            staff = GroupSerializer().create(item_data)
            staffs.append(staff)

        return staffs

    def update(self, validated_data):
        items_data = validated_data.pop("items")
        staffs = []

        for item_data in items_data:
            staff = GroupSerializer().update(item_data)
            staffs.append(staff)

        return staffs
