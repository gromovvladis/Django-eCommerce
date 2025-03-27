from core.loading import get_model
from django import forms

UserAddress = get_model("address", "UserAddress")


class BaseUserAddressForm(forms.ModelForm):
    """Базовая форма адреса с общими настройками"""

    common_attrs = {
        "class": "input d-flex align-center input__label-active input__padding"
    }
    hidden_fields = {
        "coords_long": forms.HiddenInput(),
        "coords_lat": forms.HiddenInput(),
    }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.user = user if user.is_authenticated else None


class UserAddressForm(BaseUserAddressForm):
    class Meta:
        model = UserAddress
        fields = (
            "line1",
            "line2",
            "line3",
            "line4",
            "notes",
            "coords_long",
            "coords_lat",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("line1", "line2", "line3", "line4", "notes"):
            self.fields[field].widget.attrs.update(self.common_attrs)
        self.fields["coords_long"].widget = self.hidden_fields["coords_long"]
        self.fields["coords_lat"].widget = self.hidden_fields["coords_lat"]


class UserLiteAddressForm(BaseUserAddressForm):
    class Meta:
        model = UserAddress
        fields = ("line1", "coords_long", "coords_lat")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["line1"].widget.attrs.update(self.common_attrs)
        self.fields["coords_long"].widget = self.hidden_fields["coords_long"]
        self.fields["coords_lat"].widget = self.hidden_fields["coords_lat"]
