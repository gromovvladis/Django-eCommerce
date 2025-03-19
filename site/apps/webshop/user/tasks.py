from celery import shared_task
from apps.sms.utils import get_provider_class


@shared_task
def send_sms_async(phone_number, message):
    provider_class = get_provider_class()
    provider = provider_class(
        to=phone_number, message=message, conf=get_provider_class()
    )
    provider.send_sms()
