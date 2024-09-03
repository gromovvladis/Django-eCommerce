import datetime
import phonenumbers

from django import forms
from django.conf import settings
from django.contrib.auth import forms as auth_forms
from django.contrib.sites.shortcuts import get_current_site
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.module_loading import import_string

from phonenumber_field.modelfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber

from oscar.apps.customer.utils import get_password_reset_url, normalise_email
from oscar.core.compat import existing_user_fields, get_user_model
from oscar.core.loading import get_class, get_model
from oscar.core.utils import datetime_combine

CustomerDispatcher = get_class("customer.utils", "CustomerDispatcher")
User = get_user_model()


class UserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
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
                raise ValidationError("Пользователь с таким адресом электронной почты уже существует")
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
        widget=forms.TextInput(attrs={
            'placeholder': '+7 (900) 000 0000',
            'inputmode': 'tel',
        })
    )

    password = forms.CharField(
        label="СМС код",
        max_length=4,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '0000',
            'inputmode': 'numeric',
        }),
        validators=[validators.RegexValidator(r'^\d{1,10}$')]
    )

    redirect_url = forms.CharField(widget=forms.HiddenInput, required=False)
    
    error_messages = {
        "invalid_login": "Пожалуйста, введите корректный номер телефона.",
        "inactive": "Этот аккаунт не активен.",
    }

    def __init__(self, host, *args, **kwargs):
        self.host = host
        self.request = kwargs.pop('request')
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

            backend = import_string(settings.PHONE_BACKEND)()

            self.user_cache = backend.authenticate(
                request=self.request, username=phone_number, password=code
            )
            
            if self.user_cache is None:
                return
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.user_cache


    def clean_redirect_url(self):
        url = self.cleaned_data["redirect_url"].strip()
        if url and url_has_allowed_host_and_scheme(url, self.host):
            return url
        

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
            phone_number = PhoneNumber.from_string(number, region='RU')
            if not phone_number.is_valid():
                self.add_error(
                    field_name, "Это недопустимый формат телефона."
                )
        except phonenumbers.NumberParseException:
            self.add_error(
                field_name, "Это недействительный формат телефона.",
            )
            return number

        return phone_number


    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['username'] = self.clean_phone_number_field('username')
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
    redirect_url = forms.CharField(widget=forms.HiddenInput, required=False)

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

    def clean_redirect_url(self):
        url = self.cleaned_data["redirect_url"].strip()
        if url and url_has_allowed_host_and_scheme(url, self.host):
            return url
        return settings.LOGIN_REDIRECT_URL

    def save(self, commit=True):
        user = super().save(commit=commit)
        return user
    

class PasswordResetForm(auth_forms.PasswordResetForm):
    """
    This form takes the same structure as its parent from :py:mod:`django.contrib.auth`
    """

    def save(self, *args, domain_override=None, request=None, **kwargs):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        site = get_current_site(request)
        if domain_override is not None:
            site.domain = site.name = domain_override
        for user in self.get_users(self.cleaned_data["email"]):
            self.send_password_reset_email(site, user, request)

    def send_password_reset_email(self, site, user, request=None):
        extra_context = {
            "user": user,
            "site": site,
            "reset_url": get_password_reset_url(user),
            "request": request,
        }
        CustomerDispatcher().send_password_reset_email_for_user(user, extra_context)


class OrderSearchForm(forms.Form):

    date_range = forms.CharField(
        required=False,
        label=("Даты заказов"),
    )
    order_number = forms.CharField(required=False, label="Номер заказа")

    def clean(self):
        if self.is_valid() and not any(
            [
                self.cleaned_data["date_range"],
                self.cleaned_data["order_number"],
            ]
        ):
            raise forms.ValidationError("Требуется хотя бы одно поле.")
        return super().clean()

    def description(self):
        """
        Uses the form's data to build a useful description of what orders
        are listed.
        """
        if not self.is_bound or not self.is_valid():
            return
            # return "Все заказы"
        else:
            date_range = self.cleaned_data["date_range"].split(' - ')
            date_from = None
            date_to = None

            if len(date_range) > 0:
                date_from = datetime.datetime.strptime(date_range[0], "%d.%m.%Y").date()

            if len(date_range) > 1:
                date_to = datetime.datetime.strptime(date_range[1], "%d.%m.%Y").date()

            order_number = self.cleaned_data["order_number"]
            return self._orders_description(date_from, date_to, order_number)

    def _orders_description(self, date_from, date_to, order_number):
        if date_from and date_to:
            if order_number:
                desc = (
                    "Заказы, размещенные между %(date_from)s и "
                    "%(date_to)s и номером заказа содержащий: "
                    "%(order_number)s"
                )
            else:
                desc = "Заказы размещены между %(date_from)s и %(date_to)s"
        elif date_from:
            if order_number:
                desc = (
                    "Заказы размещены с %(date_from)s и "
                    "номер заказа, содержащий %(order_number)s"
                )
            else:
                desc = "Заказы размещены с %(date_from)s"
        elif date_to:
            if order_number:
                desc = (
                    "Заказы размещены до %(date_to)s и "
                    "номер заказа, содержащий %(order_number)s"
                )
            else:
                desc = "Заказы размещены до %(date_to)s"
        elif order_number:
            desc = "Заказы с номером заказа, содержащий номер %(order_number)s"
        else:
            return None
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "order_number": order_number,
        }
        return desc % params

    def get_filters(self):
        date_range = self.cleaned_data["date_range"].split(' - ')
        date_from = None
        date_to = None

        if len(date_range) > 0:
            date_from = datetime.datetime.strptime(date_range[0], "%d.%m.%Y").date()

        if len(date_range) > 1:
            date_to = datetime.datetime.strptime(date_range[1], "%d.%m.%Y").date()

        order_number = self.cleaned_data["order_number"]
        kwargs = {}
        if date_from:
            kwargs["date_placed__gte"] = datetime_combine(date_from, datetime.time.min)
        if date_to:
            kwargs["date_placed__lte"] = datetime_combine(date_to, datetime.time.max)
        if order_number:
            kwargs["number__contains"] = order_number
        return kwargs











# def generate_username():
#     letters = string.ascii_letters
#     allowed_chars = letters + string.digits + "_"
#     uname = get_random_string(length=10, allowed_chars=allowed_chars)
#     try:
#         User.objects.get(username=uname)
#         return generate_username()
#     except User.DoesNotExist:
#         return uname


# class PhoneSmsForm(forms.Form):

#     username = forms.CharField(
#         label="Телефон",
#         required=True,
#         max_length=12,
#         validators=[validators.RegexValidator(regex = r"^\+?1?\d{8,15}$")]
#     )

#     error_messages = {
#         "invalid_login": "Пожалуйста, введите корректный номер телефона.",
#         "inactive": "Этот аккаунт не активен.",
#     }


#     def __init__(self, host, *args, **kwargs):
#         self.host = host
#         self.request = kwargs.pop('request')
#         self.user_cache = None
#         super().__init__(*args, **kwargs)


#     def get_phone(self):
#         phone_number = self.cleaned_data.get("username")
#         return phone_number


#     def get_invalid_login_error(self):
#         messages.error(self.request, 'Invalid code')


#     def clean_redirect_url(self):
#         url = self.cleaned_data["redirect_url"].strip()
#         if url and url_has_allowed_host_and_scheme(url, self.host):
#             return url




# class ConfirmPasswordForm(forms.Form):
#     """
#     Extends the standard django AuthenticationForm, to support 75 character
#     usernames. 75 character usernames are needed to support the EmailOrUsername
#     authentication backend.
#     """

#     password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

#     def __init__(self, user, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.user = user

#     def clean_password(self):
#         password = self.cleaned_data["password"]
#         if not self.user.check_password(password):
#             raise forms.ValidationError("Введенный пароль недействителен!")
#         return password




# Profile = get_profile_class()
# if Profile:

#     class UserAndProfileForm(forms.ModelForm):
#         def __init__(self, user, *args, **kwargs):
#             try:
#                 instance = Profile.objects.get(user=user)
#             except Profile.DoesNotExist:
#                 # User has no profile, try a blank one
#                 instance = Profile(user=user)
#             kwargs["instance"] = instance

#             super().__init__(*args, **kwargs)

#             # Get profile field names to help with ordering later
#             profile_field_names = list(self.fields.keys())

#             # Get user field names (we look for core user fields first)
#             core_field_names = set([f.name for f in User._meta.fields])
#             user_field_names = ["email"]
#             for field_name in ("first_name", "last_name"):
#                 if field_name in core_field_names:
#                     user_field_names.append(field_name)
#             user_field_names.extend(User._meta.additional_fields)

#             # Store user fields so we know what to save later
#             self.user_field_names = user_field_names

#             # Add additional user form fields
#             additional_fields = forms.fields_for_model(User, fields=user_field_names)
#             self.fields.update(additional_fields)

#             # Ensure email is required and initialised correctly
#             self.fields["email"].required = True

#             # Set initial values
#             for field_name in user_field_names:
#                 self.fields[field_name].initial = getattr(user, field_name)

#             # Ensure order of fields is email, user fields then profile fields
#             self.field_order = user_field_names + profile_field_names
#             self.order_fields(self.field_order)

#         class Meta:
#             model = Profile
#             # pylint: disable=modelform-uses-exclude
#             exclude = ("user",)

#         def clean_email(self):
#             email = normalise_email(self.cleaned_data["email"])

#             users_with_email = User._default_manager.filter(
#                 email__iexact=email
#             ).exclude(id=self.instance.user.id)
#             if users_with_email.exists():
#                 raise ValidationError("Пользователь с таким адресом электронной почты уже существует")
#             return email

#         def save(self, *args, **kwargs):
#             user = self.instance.user

#             # Save user also
#             for field_name in self.user_field_names:
#                 setattr(user, field_name, self.cleaned_data[field_name])
#             user.save()

#             return super().save(*args, **kwargs)

#     ProfileForm = UserAndProfileForm
# else:
#     ProfileForm = UserForm
# 



# class ProductAlertForm(forms.ModelForm):
#     email = forms.EmailField(
#         required=True,
#         label="Отправить уведомление на",
#         widget=forms.TextInput(attrs={"placeholder": "Введите адрес электронной почты"}),
#     )

#     def __init__(self, user, product, *args, **kwargs):
#         self.user = user
#         self.product = product
#         super().__init__(*args, **kwargs)

#         # Only show email field to unauthenticated users
#         if user and user.is_authenticated:
#             self.fields["email"].widget = forms.HiddenInput()
#             self.fields["email"].required = False

#     def save(self, commit=True):
#         alert = super().save(commit=False)
#         if self.user.is_authenticated:
#             alert.user = self.user
#         alert.product = self.product
#         if commit:
#             alert.save()
#         return alert

#     def clean(self):
#         cleaned_data = self.cleaned_data
#         email = cleaned_data.get("email")
#         if email:
#             try:
#                 ProductAlert.objects.get(
#                     product=self.product,
#                     email__iexact=email,
#                     status=ProductAlert.ACTIVE,
#                 )
#             except ProductAlert.DoesNotExist:
#                 pass
#             else:
#                 raise forms.ValidationError("Уже есть активное оповещение о запасах %s" % email)

#             # Check that the email address hasn't got other unconfirmed alerts.
#             # If they do then we don't want to spam them with more until they
#             # have confirmed or cancelled the existing alert.
#             if ProductAlert.objects.filter(
#                 email__iexact=email, status=ProductAlert.UNCONFIRMED
#             ).count():
#                 raise forms.ValidationError(
#                         "%s было отправлено электронное письмо с подтверждением для другого продукта"
#                         "предупреждение на этом сайте. Пожалуйста, подтвердите или отмените этот запрос"
#                         "прежде чем подписаться на дополнительные оповещения." % email
#                 )
#         elif self.user.is_authenticated:
#             try:
#                 ProductAlert.objects.get(
#                     product=self.product, user=self.user, status=ProductAlert.ACTIVE
#                 )
#             except ProductAlert.DoesNotExist:
#                 pass
#             else:
#                 raise forms.ValidationError("У вас уже есть активное оповещение для этого продукта.")
#         return cleaned_data

#     class Meta:
#         model = ProductAlert
#         fields = ["email"]
