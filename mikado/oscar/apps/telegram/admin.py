from django.contrib import admin
from oscar.core.loading import get_model

TelegramMassage = get_model("telegram", "TelegramMassage")
TelegramUser = get_model("telegram", "TelegramUser")

admin.site.register(TelegramMassage)
admin.site.register(TelegramUser)
