import phonenumbers
from django import forms
from django.core import validators
from phonenumber_field.phonenumber import PhoneNumber


class PhoneNumberMixin(object):
    """Validation mixin for forms with a phone numbers, and optionally a country.

    It tries to validate the phone numbers, and on failure tries to validate
    them using a hint (the country provided), and treating it as a local number.

    Specify which fields to treat as phone numbers by specifying them in
    `phone_number_fields`, a dictionary of fields names and default kwargs
    for instantiation of the field.
    """

    # Since this mixin will be used with `ModelForms`, names of phone number
    # fields should match names of the related Model field
    phone_number_fields = {
        "phone_number": {
            "required": False,
            "help_text": "",
            "max_length": 32,
            "label": "Номер телефона",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # We can't use the PhoneNumberField here since we want validate the
        # phonenumber based on the selected country as a fallback when a local
        # number is entered. We add the fields in the init since on Python 2
        # using forms.Form as base class results in errors when using this
        # class as mixin.

        # If the model field already exists, copy existing properties from it
        for field_name, field_kwargs in self.phone_number_fields.items():
            for key in field_kwargs:
                try:
                    field_kwargs[key] = getattr(self.fields[field_name], key)
                except (KeyError, AttributeError):
                    pass

            self.fields[field_name] = forms.CharField(**field_kwargs)

    def clean_phone_number_field(self, field_name):
        number = self.cleaned_data.get(field_name)

        # Empty
        if number in validators.EMPTY_VALUES:
            return ""

        # Check for an international phone format
        try:
            phone_number = PhoneNumber.from_string(number)
        except phonenumbers.NumberParseException:

            try:
                phone_number = PhoneNumber.from_string(number, region="RU")
                if not phone_number.is_valid():
                    self.add_error(field_name, "Это недопустимый формат телефона")
            except phonenumbers.NumberParseException:
                # Not a valid local or international phone number
                self.add_error(
                    field_name,
                    "Это недействительный формат местного или международного телефона",
                )
                return number

        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        for field_name in self.phone_number_fields:
            cleaned_data[field_name] = self.clean_phone_number_field(field_name)
        return cleaned_data
