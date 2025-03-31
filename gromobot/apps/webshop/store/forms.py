from core.loading import get_model
from django import forms
from django.core.cache import cache

Store = get_model("store", "Store")


class StoreSelectForm(forms.Form):
    store_id = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect,
        label="ID Магазина",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_initail_stores()

    def set_initail_stores(self):
        self.stores = cache.get_or_set(
            "stores",
            lambda: Store.objects.prefetch_related("address", "users").all(),
            7200,
        )
        self.fields["store_id"].choices = [
            (store.id, store.name) for store in self.stores if store.is_active
        ]
