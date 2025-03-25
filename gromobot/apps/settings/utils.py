from core.loading import get_model
from django.core.cache import cache

Settings = get_model("settings", "Settings")


def load_settings():
    settings = cache.get("settings")

    if not settings:
        settings = Settings.objects.prefetch_related("products").filter(is_active=True)
    cache.set("settings", settings, 7200)

    return settings
