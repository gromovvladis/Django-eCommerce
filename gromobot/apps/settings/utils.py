from core.loading import get_model
from django.core.cache import cache

Settings = get_model("settings", "Settings")


def load_settings():
    return cache.get_or_set(
        "settings",
        lambda: Settings.objects.prefetch_related("products").filter(is_active=True),
        7200,
    )
