import logging
from core.loading import get_model
from django import template
from django.conf import settings
from django.core.cache import cache

Store = get_model("store", "Store")
register = template.Library()

store_default = settings.STORE_DEFAULT

logger = logging.getLogger("apps.store")


@register.simple_tag
def selected_store(request):
    try:
        stores = cache.get_or_set(
            "stores",
            lambda: Store.objects.prefetch_related("address", "users").all(),
            7200,
        )
        store_id = request.store.id or store_default
        return stores.get(id=store_id)

    except Store.DoesNotExist as e:
        logger.error(
            "Ошибка при попытке получить Магазин по его id в шаблонном теге 'selected_store' id=%s",
            e,
        )
