from django.apps import AppConfig
from django.urls import include, path

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class SmsConfig(OscarConfig):
    name = "apps.sms_auth"
    verbose_name = "SMS auth"
    namespace = "sms_auth"

    def ready(self):
        pass
        # from apps.sms_auth.listeners import phone_code_post_save

    def get_urls(self):
        urls = [
            path('', include('apps.sms_auth.api.urls'), name='sms_auth')
        ]
        return self.post_process_urls(urls)