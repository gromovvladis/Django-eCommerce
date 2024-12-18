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
        store_id_list = []

        stores_select = cache.get('stores_select')
        if not stores_select:
            stores_select = Store.objects.prefetch_related("addresses").filter(is_active=True)
            cache.set("stores_select", stores_select, 21600)
        
        for store in stores_select:
            store_id_list.append((store.id, store.name))

        self.fields["store_id"].choices = store_id_list
        self.stores = stores_select