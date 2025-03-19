from django.contrib import admin
from core.loading import get_model

TelegramMessage = get_model("telegram", "TelegramMessage")

admin.site.register(TelegramMessage)
