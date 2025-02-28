from django import forms

from oscar.core.loading import get_model

Store = get_model("store", "Store")


class EvotorStoreForm(forms.Form):
    store = forms.ChoiceField(label="Магазин", required=False, choices=())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        stores = self.store_choices()
        self.fields["store"].choices = stores
        if stores:
            self.fields["store"].initial = stores[0][0]

    def store_choices(self):
        return tuple(
            [
                (src.evotor_id, src.name)
                for src in Store.objects.filter(evotor_id__isnull=False, is_active=True)
            ]
        )
