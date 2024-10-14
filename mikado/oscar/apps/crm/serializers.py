from rest_framework import serializers

class CRMUserRegisterSerializer(serializers.Serializer):
    userId = serializers.CharField(max_length=20)
    customField = serializers.CharField(required=False, allow_blank=True)

class CRMUserLoginSerializer(serializers.Serializer):
    userId = serializers.CharField(max_length=20)