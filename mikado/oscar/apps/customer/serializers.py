import logging
from rest_framework import serializers   
from django.contrib.auth.models import Group
from oscar.apps.customer.models import GroupEvotor
from oscar.core.loading import get_model

logger = logging.getLogger("oscar.customer")

User = get_model("user", "User")
Staff = get_model("user", "Staff")
Partner = get_model("partner", "Partner")

class UserGroupSerializer(serializers.ModelSerializer):
    name = serializers.CharField() 
    id = serializers.CharField(write_only=True) 
    class Meta:
        model = Group
        fields = ['name', 'id']

    
    def create(self, validated_data):
        # Извлекаем адрес из данных, если передан
        evotor_data = validated_data.pop('id', None)

        # Создаем объект партнера
        group = Group.objects.create(**validated_data)

        # Если адрес передан, сохраняем его как отдельную запись в PartnerAddress
        if evotor_data:
            GroupEvotor.objects.create(group=group, evotor_id=evotor_data)

        return group
    
    def update(self, instance, validated_data):
        # Обновляем имя группы, если оно передано
        instance.name = validated_data.get('name', instance.name)
        instance.save()

        # Получаем новый evotor_id из данных
        evotor_data = validated_data.get('id', None)

        if evotor_data:
            # Пытаемся найти существующую запись GroupEvotor для этой группы
            try:
                group_evotor = GroupEvotor.objects.get(group=instance)
                group_evotor.evotor_id = evotor_data  # Обновляем evotor_id
                group_evotor.save()
            except GroupEvotor.DoesNotExist:
                # Если записи GroupEvotor нет, создаем её
                GroupEvotor.objects.create(group=instance, evotor_id=evotor_data)

        return instance


class StaffSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='evotor_id')
    name = serializers.CharField(source='first_name')
    last_name = serializers.CharField(required=False)
    patronymic_name = serializers.CharField(source='middle_name', required=False, allow_blank=True)

    phone = serializers.CharField(write_only=True, required=False)
    stores = serializers.ListField(write_only=True, required=False)
    role = serializers.CharField(write_only=True, required=False)
    role_id = serializers.CharField(write_only=True, required=False)

    updated_at = serializers.DateTimeField(write_only=True) 

    class Meta:
        model = Staff
        fields = ['id', 'name', 'last_name', 'patronymic_name', 'phone', 'stores', 'role', 'role_id', 'updated_at']

    def create(self, validated_data):
        # Извлекаем адрес из данных, если передан
        updated_at = validated_data.pop('updated_at', None)
        phone_data = validated_data.pop('phone', None)
        partners_data = validated_data.pop('stores', None)
        role_data = validated_data.pop('role', None)
        role_id_data = validated_data.pop('role_id', None)

        # Получаем или создаем пользователя, проверяя на существование по username
        if phone_data:
            user, created = User.objects.get_or_create(
                username=phone_data, 
                defaults={'is_staff': True, 'name': validated_data.get('first_name', "")}
                )        
            # Если пользователь уже существовал, обновляем его данные, если они отличаются
            if not created:
                user.is_staff = True
                user.name = validated_data.get('first_name', "")
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
        phone_data = validated_data.pop('phone', None)
        partners_data = validated_data.pop('stores', None)
        role_data = validated_data.pop('role', None)
        role_id_data = validated_data.pop('role_id', None)

        # Обновляем данные пользователя
        if phone_data:
            user, created = User.objects.get_or_create(
            username=phone_data, 
            defaults={'is_staff': True, 'name': validated_data.get('first_name', "")}
            )
            # Если пользователь уже существовал, обновляем его данные, если они отличаются
            if not created:
                user.is_staff = True
                user.name = validated_data.get('first_name', "")
                user.save()

            instance.user = user

        # Обновляем информацию о сотруднике
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.middle_name = validated_data.get('middle_name', instance.middle_name)
        
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
            representation['stores'] = [partner.evotor_id for partner in instance.user.partners.all()]
            representation['phone'] = str(instance.user.username)
            role = instance.role.evotor
            if role:
                representation['role_id'] = role.evotor_id
        except Exception as e:
            logger.error("Ошибка определения списка магазинов сотрудника", e)
            representation['stores'] = []
            representation['phone'] = ""
            representation['role_id'] = ""
        return representation

     
class StaffsSerializer(serializers.ModelSerializer):
    items = StaffSerializer(many=True)

    class Meta:
        model = Staff
        fields = ['items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        staffs = []

        for item_data in items_data:
            staff = StaffSerializer().create(item_data)
            staffs.append(staff)

        return staffs

    def update(self, validated_data):
        items_data = validated_data.pop('items')
        staffs = []

        for item_data in items_data:
            staff = StaffSerializer().update(item_data)
            staffs.append(staff)

        return staffs
