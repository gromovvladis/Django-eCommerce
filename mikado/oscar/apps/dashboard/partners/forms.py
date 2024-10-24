from django import forms
from django.contrib.auth.models import Permission
from django.contrib.auth.password_validation import validate_password
from oscar.core.compat import existing_user_fields, get_user_model
from oscar.core.loading import get_class, get_model

from oscar.forms import widgets

User = get_user_model()
Partner = get_model("partner", "Partner")
PartnerAddress = get_model("partner", "PartnerAddress")
# PhoneUserCreationForm = get_class("customer.forms", "PhoneUserCreationForm")


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


class ExistingUserForm(forms.ModelForm):
    """
    Slightly different form that makes
    * makes saving password optional
    * doesn't regenerate username
    * doesn't allow changing email till #668 is resolved
    """
    ROLE_CHOICES = (
        ("staff", "Полный доступ к панели управления"),
        ("limited", "Ограниченный доступ к панели управления"),
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES, widget=forms.RadioSelect, label="Роль пользователя"
    )
    password1 = forms.CharField(
        label="Пароль", widget=forms.PasswordInput, required=False
    )
    password2 = forms.CharField(
        required=False, label="Подтвердите пароль", widget=forms.PasswordInput
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data.get("password2", "")

        if password1 != password2:
            raise forms.ValidationError("Два поля пароля не совпадают.")
        validate_password(password2, self.instance)
        return password2

    def __init__(self, *args, **kwargs):
        user = kwargs["instance"]
        role = "staff" if user.is_staff else "limited"
        kwargs.get("initial", {}).setdefault("role", role)
        super().__init__(*args, **kwargs)

    def save(self, commit=False):
        role = self.cleaned_data.get("role", "none")
        user = super().save(commit=False)
        user.is_staff = role == "staff"
        if self.cleaned_data["password1"]:
            user.set_password(self.cleaned_data["password1"])
        user.save()

        # dashboard_perm = Permission.objects.get(
        #     codename="dashboard_access", content_type__app_label="partner"
        # )
        # user_has_perm = user.user_permissions.filter(pk=dashboard_perm.pk).exists()
        # if role == "limited" and not user_has_perm:
        #     user.user_permissions.add(dashboard_perm)
        # elif role == "staff" and user_has_perm:
        #     user.user_permissions.remove(dashboard_perm)
        return user

    class Meta:
        model = User
        fields = existing_user_fields(["name"]) + [
            "password1",
            "password2",
        ]


class UserPhoneForm(forms.Form):
    # We use a CharField so that a partial phone can be entered
    username = forms.CharField(label="Номер телефона сотрудника", max_length=20)


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
