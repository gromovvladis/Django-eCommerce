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
        stores = cache.get("stores")
        if stores is None:
            stores = Store.objects.prefetch_related("addresses", "users").all()
            cache.set("stores", stores, 21600)

        store_id = request.store.id or store_default
        return stores.get(id=store_id)
    
    except Store.DoesNotExist:
        return None
