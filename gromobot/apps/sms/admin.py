from core.loading import get_model
from django.contrib.admin import ModelAdmin, register

SMSMessage = get_model("sms", "SMSMessage")
AuthCode = get_model("sms", "AuthCode")


@register(SMSMessage)
class SMSMessageAdmin(ModelAdmin):
    readonly_fields = (
        "created",
        "phone_number",
    )

    def has_add_permission(self, request):
        return False


@register(AuthCode)
class AuthCodeAdmin(ModelAdmin):
    readonly_fields = (
        "valid_to",
        "created_at",
    )
