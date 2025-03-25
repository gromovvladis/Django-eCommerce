from core.loading import get_model
from django.contrib import admin

Settings = get_model("settings", "Settings")

admin.site.register(Settings)
