from core.loading import get_model
from django.contrib import admin

TelegramMessage = get_model("telegram", "TelegramMessage")

admin.site.register(TelegramMessage)
