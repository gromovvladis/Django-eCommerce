from rest_framework import serializers   
from django.contrib.auth.models import Group
from oscar.apps.customer.models import GroupEvotor
from oscar.core.loading import get_model

User = get_model("user", "User")
Staff = get_model("user", "Staff")
Partner = get_model("partner", "Partner")

class GroupSerializer(serializers.ModelSerializer):
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
    last_name = serializers.CharField()
    patronymic_name = serializers.CharField(source='middle_name')

    phone = serializers.CharField(write_only=True)
    stores = serializers.ListField(write_only=True)
    role = serializers.CharField(write_only=True)
    role_id = serializers.CharField(write_only=True)

    class Meta:
        model = Staff
        fields = ['id', 'name', 'last_name', 'patronymic_name', 'role', 'phone', 'stores', 'role_id']

    def create(self, validated_data):
        # Извлекаем адрес из данных, если передан
        phone_data = validated_data.pop('phone', None)
        partners_data = validated_data.pop('stores', None)
        role_data = validated_data.pop('role', None)
        role_id_data = validated_data.pop('role_id', None)

        user, _ = User.objects.get_or_create(username=phone_data, is_staff=True, name=validated_data.get('first_name', ""))

        staff = Staff.objects.create(user=user, **validated_data)

        if partners_data:
            partners = Partner.objects.filter(evotor_id__in=partners_data)
            for partner in partners:
                partner.users.add(staff)
        
        if role_data:
            group, _ = Group.objects.get_or_create(name=role_data)
            GroupEvotor.objects.get_or_create(group=group, evotor_id=role_id_data)
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
            user = instance.user
            user.username = phone_data
            user.name = validated_data.get('first_name', user.name)
            user.save()

        # Обновляем информацию о сотруднике
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.middle_name = validated_data.get('middle_name', instance.middle_name)
        
        # Обновляем привязку к партнёрам
        partners = Partner.objects.filter(users=instance.user)
        for partner in partners:
            partner.users.remove(instance.user)

        # Добавляем новые привязки
        if partners_data:
            new_partners = Partner.objects.filter(evotor_id__in=partners_data)
            for new_partner in new_partners:
                new_partner.users.add(instance.user)

        # Обновляем роль
        if role_data:
            group, _ = Group.objects.get_or_create(name=role_data)
            GroupEvotor.objects.get_or_create(group=group, evotor_id=role_id_data)
            instance.role = group

        instance.save()

        return instance



# class TerminalSerializer(serializers.ModelSerializer):
#     id = serializers.CharField(source='evotor_id')
#     name = serializers.CharField()
#     device_model = serializers.CharField()
#     serial_number = serializers.CharField()
#     imei = serializers.CharField()

#     store_id = serializers.CharField(write_only=True) 
#     location = serializers.JSONField(write_only=True)  

#     class Meta:
#         model = Partner
#         fields = ['id', 'name', 'device_model', 'serial_number', 'imei', 'store_id', 'location']

#     def create(self, validated_data):

#         store_id = validated_data.pop('store_id')
#         location = validated_data.pop('location', {})

#         coords_long = location.get('lng')
#         coords_lat = location.get('lat')

#         terminal = Terminal.objects.create(
#             coords_long=coords_long,
#             coords_lat=coords_lat,
#             **validated_data
#         )

#         partner, created = Partner.objects.get_or_create(evotor_id=store_id)

#         partner.terminals.add(terminal)

#         return partner
    
#     def update(self, instance, validated_data):
#         store_id = validated_data.pop('store_id')
#         location = validated_data.pop('location', {})

#         coords_long = location.get('lng')
#         coords_lat = location.get('lat')

#         # Обновляем терминал
#         instance.coords_long = coords_long
#         instance.coords_lat = coords_lat
#         instance.device_model = validated_data.get('device_model', instance.device_model)
#         instance.serial_number = validated_data.get('serial_number', instance.serial_number)
#         instance.imei = validated_data.get('imei', instance.imei)
#         instance.name = validated_data.get('name', instance.name)
        
#         instance.save()

#         # Получаем или создаем партнера
#         partner, created = Partner.objects.get_or_create(evotor_id=store_id)

#         # Удаляем терминал у других партнеров
#         other_partners = Partner.objects.all()
#         for other_partner in other_partners:
#             terminals_to_remove = other_partner.terminals.filter(id=instance.id)
#             if terminals_to_remove.exists():
#                 other_partner.terminals.remove(*terminals_to_remove)  # Удаляем терминалы

#         # Добавляем обновленный терминал к партнеру
#         partner.terminals.add(instance)

#         return partner
