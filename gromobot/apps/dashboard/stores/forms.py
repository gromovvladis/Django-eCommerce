from core.compat import get_user_model
from core.loading import get_model
from django import forms

User = get_user_model()
Store = get_model("store", "Store")
Store = get_model("store", "Store")
StoreCashTransaction = get_model("store", "StoreCashTransaction")


class StoreSearchForm(forms.Form):
    name = forms.CharField(required=False, label="Название")


class StoreForm(forms.ModelForm):
    line1 = forms.CharField(
        required=False,
        max_length=128,
        label="Улица, дом",
        widget=forms.TextInput(attrs={"readonly": "true"}),
    )
    coords_long = forms.CharField(
        required=False,
        max_length=128,
        label="Координаты долгота",
        widget=forms.HiddenInput(),
    )
    coords_lat = forms.CharField(
        required=False,
        max_length=128,
        label="Координаты широта",
        widget=forms.HiddenInput,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store.name is optional and that is okay. But if creating through
        # the dashboard, it seems sensible to enforce as it's the only field
        # in the form.
        self.fields["name"].required = True

    class Meta:
        model = Store
        fields = (
            "name",
            "line1",
            "coords_long",
            "coords_lat",
            "start_worktime",
            "end_worktime",
            "is_active",
        )
        sequence = (
            "name",
            "line1",
            "coords_long",
            "coords_lat",
            "start_worktime",
            "end_worktime",
            "is_active",
        )


class StoreCashTransactionForm(forms.ModelForm):
    def __init__(self, store, user, *args, **kwargs):
        self.store = store
        self.user = user
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        instance.store = self.store
        if commit:
            instance.save()
        return instance

    class Meta:
        model = StoreCashTransaction
        fields = (
            "type",
            "description",
            "sum",
            "store",
            "user",
        )
        exclude = ["store", "user"]
