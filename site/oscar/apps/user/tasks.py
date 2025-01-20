from oscar.apps.sms_auth.conf import conf
from celery import shared_task


def get_provider_class():
    provider = conf.SMS_PROVIDER
    return provider

@shared_task
def send_sms_async(phone_number, message):
    provider_class = get_provider_class()
    provider = provider_class(
        to=phone_number, message=message, conf=conf
    )
    provider.send_sms()
