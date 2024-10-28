from django import forms
from oscar.core.compat import  get_user_model
from oscar.core.loading import  get_model

User = get_user_model()
Partner = get_model("partner", "Partner")
PartnerAddress = get_model("partner", "PartnerAddress")


class PartnerSearchForm(forms.Form):
    name = forms.CharField(
        required=False, label="Название"
    )


class PartnerCreateForm(forms.ModelForm):

    line1 = forms.CharField(
        required=False, max_length=128, label="Улица, дом"
    )
    start_worktime = forms.TimeField(
        required=False, label="Время открытия точки"
    )
    end_worktime = forms.TimeField(
        required=False, label="Время закрытия точки"
    )
    coords_long = forms.CharField(
        required=False, max_length=128, label="Координаты долгота"
    )
    coords_lat = forms.CharField(
        required=False, max_length=128, label="Координаты широта"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Partner.name is optional and that is okay. But if creating through
        # the dashboard, it seems sensible to enforce as it's the only field
        # in the form.
        self.fields["name"].required = True

    class Meta:
        model = Partner
        fields = (
            "name",
            "start_worktime",
            "end_worktime",
        )
        widgets = {
            'line1': forms.TextInput(attrs={
                'readonly': "true"
            }),
            # 'start_worktime': forms.TextInput(attrs={
            #     'class': "time"
            # }),
            # 'end_worktime': forms.TextInput(attrs={
            #     'class': "time"
            # }),
            'coords_long': forms.TextInput(attrs={
                'readonly': "true"
            }),
            'coords_lat': forms.TextInput(attrs={
                'readonly': "true"
            }),
        }


class PartnerAddressForm(forms.ModelForm):
    name = forms.CharField(
        required=False, max_length=128, label="Название"
    )
    start_worktime = forms.TimeField(
        required=False, label="Время открытия точки"
    )
    end_worktime = forms.TimeField(
        required=False, label="Время закрытия точки"
    )

    class Meta:
        fields = (
            "name",
            "line1",
            "start_worktime",
            "end_worktime",
            "coords_long",
            "coords_lat",
        )
        widgets = {
            'line1': forms.TextInput(attrs={
                'readonly': "true"
            }),
            # "start_worktime": widgets.DateTimePickerInput(),
            # "end_worktime": widgets.DateTimePickerInput(),
            # 'start_worktime': forms.TimeInput(attrs={
            #     'class': "time"
            # }),
            # 'end_worktime': forms.TimeInput(attrs={
            #     'class': "time"
            # }),
            'coords_long': forms.TextInput(attrs={
                'readonly': "true"
            }),
            'coords_lat': forms.TextInput(attrs={
                'readonly': "true"
            }),
        }
        model = PartnerAddress
