import logging

from core.loading import get_model
from django.contrib.auth.models import Group
from rest_framework import serializers

logger = logging.getLogger("apps.webshop.customer")

User = get_model("user", "User")
Staff = get_model("user", "Staff")
Store = get_model("store", "Store")
EvotorUserGroup = get_model("evotor", "EvotorUserGroup")


class UserGroupSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    id = serializers.CharField(write_only=True)

    class Meta:
        model = Group
        fields = ["name", "id"]

    def create(self, validated_data):
        # Извлекаем адрес из данных, если передан
        evotor_data = validated_data.pop("id", None)

        # Создаем объект партнера
        group = Group.objects.create(**validated_data)

        # Если адрес передан, сохраняем его как отдельную запись в StoreAddress
        if evotor_data:
            EvotorUserGroup.objects.create(group=group, evotor_id=evotor_data)

        return group

    def update(self, instance, validated_data):
        # Обновляем имя группы, если оно передано
        instance.name = validated_data.get("name", instance.name)
        instance.save()

        # Получаем новый evotor_id из данных
        evotor_data = validated_data.get("id", None)

        if evotor_data:
            # Пытаемся найти существующую запись GroupEvotor для этой группы
            try:
                evotor_usergroup = EvotorUserGroup.objects.get(group=instance)
                evotor_usergroup.evotor_id = evotor_data  # Обновляем evotor_id
                evotor_usergroup.save()
            except EvotorUserGroup.DoesNotExist:
                # Если записи EvotorUserGroup нет, создаем её
                EvotorUserGroup.objects.create(group=instance, evotor_id=evotor_data)

        return instance


class StaffSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="evotor_id")
    name = serializers.CharField(source="first_name")
    last_name = serializers.CharField(required=False)
    patronymic_name = serializers.CharField(
        source="middle_name", required=False, allow_blank=True
    )

    phone = serializers.CharField(write_only=True, required=False)
    stores = serializers.ListField(write_only=True, required=False)
    role = serializers.CharField(write_only=True, required=False)
    role_id = serializers.CharField(write_only=True, required=False)

    updated_at = serializers.DateTimeField(write_only=True)

    class Meta:
        model = Staff
        fields = [
            "id",
            "name",
            "last_name",
            "patronymic_name",
            "phone",
            "stores",
            "role",
            "role_id",
            "updated_at",
        ]

    def create(self, validated_data):
        # Извлекаем адрес из данных, если передан
        validated_data.pop("updated_at", None)

        phone_data = validated_data.pop("phone", None)
        stores_data = validated_data.pop("stores", None)
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
            evotor_usergroup, _ = EvotorUserGroup.objects.get_or_create(group=group)
            evotor_usergroup.evotor_id = role_id_data
            evotor_usergroup.save()
            staff.role = group

        staff.save()

        return staff

    def update(self, instance, validated_data):
        # Извлекаем данные
        phone_data = validated_data.pop("phone", None)
        stores_data = validated_data.pop("stores", None)
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
            evotor_usergroup, _ = EvotorUserGroup.objects.get_or_create(group=group)
            evotor_usergroup.evotor_id = role_id_data
            evotor_usergroup.save()
            instance.role = group

        instance.save()

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop("id", None)
        try:
            representation["stores"] = [
                store.evotor_id for store in instance.user.stores.all()
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


class StaffsSerializer(serializers.ModelSerializer):
    items = StaffSerializer(many=True)

    class Meta:
        model = Staff
        fields = ["items"]

    def create(self, validated_data):
        items_data = validated_data.get("items", [])
        return [StaffSerializer().create(item_data) for item_data in items_data]

    def update(self, instances, validated_data):
        items_data = validated_data.get("items", [])
        staffs = []

        for item_data in items_data:
            try:
                staff_instance = instances.get(
                    evotor_id=item_data["id"]
                )  # `instance` — это QuerySet
                staff = StaffSerializer().update(staff_instance, item_data)
            except Staff.DoesNotExist:
                continue  # Пропускаем, если объект не найден

            staffs.append(staff)

        return staffs
