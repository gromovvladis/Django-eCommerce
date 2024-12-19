from django import forms
from oscar.core.loading import get_model

UserAddress = get_model("address", "useraddress")


class UserAddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = [
            "line1",
            "line2",
            "line3",
            "line4",
            "notes",
            "coords_long",
            "coords_lat",
        ]

        widgets = {
            'line1': forms.TextInput(attrs={
                'class' : 'input d-flex align-center input__label-active input__padding',
            }),
            'line2': forms.TextInput(attrs={
                'class' : 'input d-flex align-center input__label-active input__padding',
            }),
            'line3': forms.TextInput(attrs={
                'class' : 'input d-flex align-center input__label-active input__padding',
            }),
            'line4': forms.TextInput(attrs={
                'class' : 'input d-flex align-center input__label-active input__padding',
            }),
            'notes': forms.TextInput(attrs={
                'class' : 'input d-flex align-center input__label-active input__padding',
            }),
            'coords_long': forms.HiddenInput(),
            'coords_lat': forms.HiddenInput(),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.user = user


class UserLiteAddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = [
            "line1",
            "coords_long",
            "coords_lat",
        ]
        widgets = {
            'coords_long': forms.HiddenInput(),
            'coords_lat': forms.HiddenInput(),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.user = user