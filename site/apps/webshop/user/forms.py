import phonenumbers
from django import forms
from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string
from apps.webshop.user.utils import normalise_email
from core.compat import existing_user_fields, get_user_model
from phonenumber_field.modelfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber

User = get_user_model()


class UserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean_email(self):
        """
        Make sure that the email address is always unique as it is
        used instead of the username. This is necessary because the
        uniqueness of email addresses is *not* enforced on the model
        level in ``django.contrib.auth.models.User``.
        """

        email = normalise_email(self.cleaned_data["email"])
        if email:
            if (
                User._default_manager.filter(email__iexact=email)
                .exclude(id=self.user.id)
                .exists()
            ):
                raise ValidationError(
                    "Пользователь с таким адресом электронной почты уже существует"
                )
        # Save the email unaltered
        return email

    class Meta:
        model = User
        fields = existing_user_fields(["name", "email"])


ProfileForm = UserForm


class PhoneAuthenticationForm(forms.Form):
    """
    Extends the standard django AuthenticationForm, to support 75 character
    usernames. 75 character usernames are needed to support the EmailOrUsername
    authentication backend.
    """

    username = forms.CharField(
        label="Телефон",
        required=True,
        max_length=17,
        widget=forms.TextInput(
            attrs={
                "placeholder": "+7 (900) 000 0000",
                "inputmode": "tel",
            }
        ),
    )

    password = forms.CharField(
        label="СМС код",
        max_length=4,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "0000",
                "inputmode": "numeric",
            }
        ),
        validators=[validators.RegexValidator(r"^\d{1,10}$")],
    )

    error_messages = {
        "invalid_login": "Пожалуйста, введите корректный номер телефона.",
        "inactive": "Этот аккаунт не активен.",
    }

    def __init__(self, host, *args, **kwargs):
        self.host = host
        self.request = kwargs.pop("request")
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def confirm_login_allowed(self, user):
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``ValidationError``.

        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise ValidationError(
                self.error_messages["inactive"],
                code="inactive",
            )

    def get_user(self):
        phone_number = self.cleaned_data.get("username")
        code = self.cleaned_data.get("password")
        if phone_number is not None and code is not None:
            backend = import_string(settings.AUTH_BACKEND)()
            self.user_cache = backend.authenticate(
                request=self.request, username=phone_number, password=code
            )
            if self.user_cache is None:
                return
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.user_cache

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

    def get_phone(self):
        phone_number = self.cleaned_data.get("username")
        return phone_number

    def clean_phone_number_field(self, field_name):
        number = self.cleaned_data.get(field_name)

        try:
            phone_number = PhoneNumber.from_string(number, region="RU")
            if not phone_number.is_valid():
                self.add_error(field_name, "Это недопустимый формат телефона.")
        except phonenumbers.NumberParseException:
            self.add_error(
                field_name,
                "Это недействительный формат телефона.",
            )
            return number

        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["username"] = self.clean_phone_number_field("username")
        return cleaned_data


class PhoneUserCreationForm(forms.Form):
    phone = PhoneNumberField(
        "Номер телефона",
        blank=True,
        help_text="На случай, если нам понадобится позвонить вам по поводу вашего заказа",
    )
    sms_code = forms.CharField(
        widget=forms.widgets.TextInput,
        required=True,
        max_length=4,
    )
    error_messages = {
        "invalid_login": "Пожалуйста, введите корректный номер телефона.",
        "inactive": "Этот аккаунт не активен.",
    }

    class Meta:
        model = User
        fields = ("phone", "sms_code")

    def __init__(self, *args, host=None, **kwargs):
        self.host = host
        super().__init__(*args, **kwargs)

    def _post_clean(self):
        super()._post_clean()
        # Validate after self.instance is updated with form data
        # otherwise validators can't access email
        # see django.contrib.auth.forms.UserCreationForm

    def save(self, commit=True):
        user = super().save(commit=commit)
        return user
