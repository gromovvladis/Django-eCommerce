from django import forms
from oscar.core.loading import get_model

DeliveryZona = get_model("delivery", "DeliveryZona")


class DeliveryZonaForm(forms.ModelForm):

    def clean(self) -> None:
        cleaned_data = super().clean()
        cleaned_data["coords"] = cleaned_data["coords"].replace(" ", "")
        return cleaned_data

    class Meta:
        model = DeliveryZona
        fields = [
            "name",
            "order_price",
            "delivery_price",
            "coords",
            "isAvailable",
            "isHide",
        ]
