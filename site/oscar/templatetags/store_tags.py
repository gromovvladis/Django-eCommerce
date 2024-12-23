from django import template
from django.conf import settings
from django.core.cache import cache
from oscar.core.loading import get_model

Store = get_model("store", "Store")
register = template.Library()

store_default = settings.STORE_DEFAULT

@register.simple_tag
def selected_store(request):   
    try:
        stores_select = cache.get('stores_select')

        if not stores_select:
            stores_select = Store.objects.prefetch_related("addresses").filter(is_active=True)
            cache.set("stores_select", stores_select, 21600)  # Кэш на 6 часов

        if stores_select:
            store_id = request.store.id
            return stores_select.get(id=store_id)

        return None

    except Store.DoesNotExist:
        return None
