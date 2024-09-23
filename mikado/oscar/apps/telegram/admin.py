from django.contrib import admin
from oscar.core.loading import get_model

TelegramMassage = get_model("telegram", "TelegramMassage")

admin.site.register(TelegramMassage)
