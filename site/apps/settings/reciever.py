from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.loading import get_model

Settings = get_model("settings", "Settings")


@receiver(post_save, sender=Settings)
def clear_settings_cache(sender, instance, **kwargs):
    cache.delete("settings")
