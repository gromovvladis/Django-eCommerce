from django.core.cache import cache

from oscar.core.loading import get_model

Settings = get_model("settings", "Settings")


def load_settings():
    settings = cache.get("settings")

    if not settings:
        settings = Settings.objects.prefetch_related("products").filter(is_active=True)
    cache.set("settings", settings, 7200)

    return settings
