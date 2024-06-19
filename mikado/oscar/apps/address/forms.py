from django import forms
from oscar.core.loading import get_model

UserAddress = get_model("address", "useraddress")


class AbstractAddressForm(forms.ModelForm):
    pass


class UserAddressForm(AbstractAddressForm):
    class Meta:
        model = UserAddress
        fields = [
            "line1",
            "line2",
            "line3",
            "line4",
            "notes",
        ]

        widgets = {
            'line1': forms.TextInput(attrs={
                'class' : 'v-input d-flex align-center v-input__label-active v-input__dirty v-input__padding',
            }),
            'line2': forms.TextInput(attrs={
                'class' : 'v-input d-flex align-center v-input__label-active v-input__dirty v-input__padding',
            }),
            'line3': forms.TextInput(attrs={
                'class' : 'v-input d-flex align-center v-input__label-active v-input__dirty v-input__padding',
            }),
            'line4': forms.TextInput(attrs={
                'class' : 'v-input d-flex align-center v-input__label-active v-input__dirty v-input__padding',
            }),
            'notes': forms.TextInput(attrs={
                'class' : 'v-input d-flex align-center v-input__label-active v-input__dirty v-input__padding',
            }),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.user = user


class UserLiteAddressForm(AbstractAddressForm):
    class Meta:
        model = UserAddress
        fields = [
            "line1",
        ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.user = user