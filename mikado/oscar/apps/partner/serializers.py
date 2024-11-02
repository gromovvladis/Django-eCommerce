from rest_framework import serializers   
from .models import Partner, PartnerAddress, Terminal

class PartnerAddressSerializer(serializers.ModelSerializer):
    address = serializers.CharField(source='line1') 
    
    class Meta:
        model = PartnerAddress
        fields = ['address']


class PartnerSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='evotor_id')
    name = serializers.CharField()
    address = serializers.CharField(write_only=True, required=False) 
    updated_at = serializers.DateTimeField(write_only=True) 

    class Meta:
        model = Partner
        fields = ['id', 'name', 'address', 'updated_at']

    def create(self, validated_data):
        # Извлекаем адрес из данных, если передан
        updated_at = validated_data.pop('updated_at', None)
        address_data = validated_data.pop('address', None)
        # Создаем объект партнера
        partner = Partner.objects.create(**validated_data)

        # Если адрес передан, сохраняем его как отдельную запись в PartnerAddress
        if address_data:
            PartnerAddress.objects.create(partner=partner, line1=address_data)

        return partner

    def update(self, instance, validated_data):
        # Обновляем данные партнера
        instance.name = validated_data.get('name', instance.name)
        instance.save()

        # Обрабатываем адрес отдельно
        address_data = validated_data.get('address')
        if address_data:
            # Если адрес уже существует, обновляем его
            existing_address = PartnerAddress.objects.filter(partner=instance).first()
            if existing_address:
                existing_address.coords_long = None
                existing_address.coords_lat = None
                existing_address.line1 = address_data
                existing_address.save()
            else:
                # Создаем новый адрес, если его нет
                PartnerAddress.objects.create(partner=instance, line1=address_data)

        return instance

        
class PartnersSerializer(serializers.ModelSerializer):
    items = PartnerSerializer(many=True)

    class Meta:
        model = Partner
        fields = ['items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        partners = []

        for item_data in items_data:
            partner = PartnerSerializer().create(item_data)
            partners.append(partner)

        return partners

    def update(self, validated_data):
        items_data = validated_data.pop('items')
        partners = []

        for item_data in items_data:
            partner = PartnerSerializer().update(item_data)
            partners.append(partner)

        return partners


class TerminalSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='evotor_id')
    name = serializers.CharField()
    model = serializers.CharField(required=False)
    serial_number = serializers.CharField()
    imei = serializers.CharField(required=False)

    store_id = serializers.CharField(write_only=True) 
    location = serializers.JSONField(write_only=True, required=False)
    updated_at = serializers.DateTimeField(write_only=True)   

    class Meta:
        model = Terminal
        fields = ['id', 'name', 'model', 'serial_number', 'imei', 'store_id', 'location', 'updated_at']

    def create(self, validated_data):

        updated_at = validated_data.pop('updated_at', None)
        store_id = validated_data.pop('store_id')
        
        location = validated_data.pop('location', {})
        coords_long = location.get('lng', None)
        coords_lat = location.get('lat', None)

        terminal = Terminal.objects.create(
            coords_long=coords_long,
            coords_lat=coords_lat,
            **validated_data
        )

        partner, created = Partner.objects.get_or_create(evotor_id=store_id)
        partner.terminals.add(terminal)

        return terminal
    
    def update(self, instance, validated_data):
        store_id = validated_data.pop('store_id')
        location = validated_data.pop('location', {})

        coords_long = location.get('lng')
        coords_lat = location.get('lat')

        # Обновляем терминал
        instance.coords_long = coords_long
        instance.coords_lat = coords_lat
        instance.model = validated_data.get('model', instance.model)
        instance.serial_number = validated_data.get('serial_number', instance.serial_number)
        instance.imei = validated_data.get('imei', instance.imei)
        instance.name = validated_data.get('name', instance.name)
        
        instance.save()

        # Получаем или создаем партнера
        partner, created = Partner.objects.get_or_create(evotor_id=store_id)

        # Удаляем терминал у других партнеров
        other_partners = Partner.objects.all()
        for other_partner in other_partners:
            terminals_to_remove = other_partner.terminals.filter(id=instance.id)
            if terminals_to_remove.exists():
                other_partner.terminals.remove(*terminals_to_remove)  # Удаляем терминалы

        # Добавляем обновленный терминал к партнеру
        partner.terminals.add(instance)

        return instance

     
class TerminalsSerializer(serializers.ModelSerializer):
    items = TerminalSerializer(many=True)

    class Meta:
        model = Terminal
        fields = ['items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        terminals = []

        for item_data in items_data:
            terminal = TerminalSerializer().create(item_data)
            terminals.append(terminal)

        return terminals

    def update(self, validated_data):
        items_data = validated_data.pop('items')
        terminals = []

        for item_data in items_data:
            terminal = TerminalSerializer().update(item_data)
            terminals.append(terminal)

        return terminals
