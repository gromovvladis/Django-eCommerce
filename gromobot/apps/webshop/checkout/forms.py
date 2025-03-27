from core.compat import get_user_model
from core.loading import get_model
from django import forms
from django.conf import settings

User = get_user_model()
ShippingAddress = get_model("order", "ShippingAddress")


class CheckoutVoucherForm(forms.Form):
    code = forms.CharField(
        max_length=128,
        label="Промокод",
        widget=forms.TextInput(attrs={"class": "input"}),
    )

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()


class CheckoutForm(forms.ModelForm, forms.Form):
    method_code = forms.ChoiceField(
        label="Выберите способ доставки", widget=forms.HiddenInput
    )
    order_time = forms.DateTimeField(
        required=False,
        widget=forms.HiddenInput(),
        localize=True,
        input_formats=["%d.%m.%Y %H:%M"],
    )
    order_note = forms.CharField(
        label="Комментарий к заказу",
        widget=forms.Textarea(
            attrs={
                "class": "input text-area d-flex align-center input__padding",
                "rows": 2,
            }
        ),
        required=False,
    )
    email_or_change = forms.CharField(
        label="Эмаил для чеков или поле для сдачи",
        widget=forms.TextInput(
            attrs={
                "class": "input text-area d-flex align-center input__padding",
            }
        ),
        required=False,
    )
    payment_method = forms.ChoiceField(
        label="Выберите метод оплаты",
        choices=settings.WEBSHOP_PAYMENT_CHOICES,
        initial=settings.WEBSHOP_PAYMENT_CHOICES[0],
        widget=forms.Select(
            attrs={
                "class": "fill-width button--grey justify-space-between shrink",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        methods = kwargs.pop("methods", [])
        super().__init__(*args, **kwargs)
        self.fields["method_code"].choices = ((m.code, m.name) for m in methods)
        self.fields["method_code"].initial = self.fields["method_code"].choices[0][0]

    class Meta:
        model = ShippingAddress
        fields = (
            "line1",
            "line2",
            "line3",
            "line4",
            "notes",
            "coords_long",
            "coords_lat",
        )

        widgets = {
            "line1": forms.TextInput(
                attrs={
                    "class": "input d-flex align-center input__padding",
                    "placeholder": "Введите адрес доставки",
                }
            ),
            "line2": forms.NumberInput(
                attrs={
                    "class": "input d-flex align-center input__padding",
                    "min": 1,
                    "max": 1000,
                }
            ),
            "line3": forms.NumberInput(
                attrs={
                    "class": "input d-flex align-center input__padding",
                    "min": 1,
                    "max": 100,
                }
            ),
            "line4": forms.NumberInput(
                attrs={
                    "class": "input d-flex align-center input__padding",
                    "min": 1,
                    "max": 100,
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "input d-flex align-center input__padding",
                    "rows": 2,
                }
            ),
            "coords_long": forms.HiddenInput(),
            "coords_lat": forms.HiddenInput(),
        }
