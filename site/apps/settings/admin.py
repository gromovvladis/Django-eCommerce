from django.contrib import admin
from core.loading import get_model

Settings = get_model("settings", "Settings")

admin.site.register(Settings)
