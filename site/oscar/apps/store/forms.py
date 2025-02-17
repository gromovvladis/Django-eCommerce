from django import forms
from django.core.cache import cache

from oscar.core.loading import get_model

Store = get_model("store", "Store")


class StoreSelectForm(forms.Form):
    store_id = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect,
        label="ID Магазина",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        stores = cache.get("stores")
        if not stores:
            stores = Store.objects.prefetch_related("address", "users").all()
            cache.set("stores", stores, 21600)

        self.fields["store_id"].choices = [
            (store.id, store.name) for store in stores if store.is_active
        ]
        self.stores = stores
