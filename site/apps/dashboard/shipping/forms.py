from django import forms
from core.loading import get_model

ShippingZona = get_model("shipping", "ShippingZona")


class ShippingZonaForm(forms.ModelForm):

    def clean(self) -> None:
        cleaned_data = super().clean()
        cleaned_data["coords"] = cleaned_data["coords"].replace(" ", "")
        return cleaned_data

    class Meta:
        model = ShippingZona
        fields = [
            "name",
            "order_price",
            "shipping_price",
            "min_shipping_time",
            "coords",
            "isAvailable",
            "isHide",
        ]
