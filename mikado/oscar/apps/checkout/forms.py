from django import forms
from django.conf import settings

from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model

User = get_user_model()
AbstractAddressForm = get_class("address.forms", "AbstractAddressForm")


class CheckoutVoucherForm(forms.Form):
    code = forms.CharField(max_length=128, label="Промокод", widget=forms.TextInput(attrs={'class' : 'v-input'}))

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()


class CheckoutForm(AbstractAddressForm, forms.Form): 

    method_code = forms.ChoiceField(label="Выберите способ доставки",widget=forms.HiddenInput)

    order_time = forms.DateTimeField(
        required=False, 
        widget=forms.HiddenInput(),
        localize=True,
        input_formats = ['%d.%m.%Y %H:%M'],
    )

    order_note = forms.CharField(
        label="Комментарий к заказу", 
        widget=forms.Textarea(attrs = {
                'class' : 'v-input v-text-area d-flex align-center v-input__padding',
                'rows': 2,
        }), 
        required=False
    )

    email_or_change = forms.CharField(
        label="Эмаил для чеков или поле для сдачи", 
        widget=forms.TextInput(attrs = {
                'class' : 'v-input v-text-area d-flex align-center v-input__padding',
        }), 
        required=False
    )

    payment_method = forms.ChoiceField(
        label="Выберите метод оплаты",
        choices=settings.WEBSHOP_PAYMENT_CHOICES,
        initial=settings.WEBSHOP_PAYMENT_CHOICES[0],
        widget=forms.Select(attrs = {
                'class' : 'fill-width v-button--grey justify-space-between shrink',
        }),
    )

    def __init__(self, *args, **kwargs):
        methods = kwargs.pop("methods", [])
        super().__init__(*args, **kwargs)
        self.fields["method_code"].choices = ((m.code, m.name) for m in methods)
        self.fields["method_code"].initial = self.fields["method_code"].choices[0][0]


    class Meta:
        model = get_model("order", "shippingaddress")
        fields = [
            "line1",
            "line2",
            "line3",
            "line4",
            "notes",
        ]
        
        widgets = {
            'line1': forms.TextInput(attrs={
                'class' : 'v-input d-flex align-center v-input__padding',
                'placeholder': "Введите адрес доставки"
            }),
            'line2': forms.NumberInput(attrs={
                'class' : 'v-input d-flex align-center v-input__padding',
                'min': 1,
                'max': 1000,
            }),
            'line3': forms.NumberInput(attrs={
                'class' : 'v-input d-flex align-center v-input__padding',
                'min': 1,
                'max': 100,
            }),
            'line4': forms.NumberInput(attrs={
                'class' : 'v-input d-flex align-center v-input__padding',
                'min': 1,
                'max': 100,
            }),
            'notes': forms.Textarea(attrs={
                'class' : 'v-input d-flex align-center v-input__padding',
                'rows': 2,
            }),
        }
