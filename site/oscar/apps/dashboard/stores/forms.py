from django import forms
from oscar.core.compat import get_user_model
from oscar.core.loading import get_model

User = get_user_model()
Store = get_model("store", "Store")
StoreAddress = get_model("store", "StoreAddress")


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