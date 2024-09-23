
from django.urls import path
from oscar.core.loading import get_class
from oscar.core.application import OscarConfig

class TelegramConfig(OscarConfig):
    label = "telegram"
    name = "oscar.apps.telegram"
    verbose_name = "Телеграм"

    namespace = "telegram"