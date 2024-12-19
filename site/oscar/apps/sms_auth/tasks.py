from oscar.apps.sms_auth.services.clean import CleanService

from .conf import conf
from .models import PhoneCode
from celery import shared_task


def get_provider_class():
    provider = conf.SMS_PROVIDER
    return provider

@shared_task
def send_sms_async(identifier: int):
    code_instance = PhoneCode.objects.filter(pk=identifier).first()
    if code_instance:
        provider_class = get_provider_class()
        provider = provider_class(
            to=code_instance.phone_number, message=code_instance.message, conf=conf
        )
        provider.send_sms()

@shared_task
def clear_expired():
    CleanService.clear()
