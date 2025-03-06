import re
from datetime import date
from calendar import monthrange

from django import forms
from django.core import validators
from django.core.exceptions import ImproperlyConfigured

from oscar.core.loading import get_model
from . import bankcards

Bankcard = get_model("payment", "Bankcard")

# List of card names for all the card types supported in payment.bankcards
VALID_CARDS = set([card_type[0] for card_type in bankcards.CARD_TYPES])


class BankcardNumberField(forms.CharField):
    def __init__(self, *args, **kwargs):
        _kwargs = {
            "max_length": 20,
            "widget": forms.TextInput(attrs={"autocomplete": "off"}),
            "label": "Номер карты",
        }
        if "types" in kwargs:
            self.accepted_cards = set(kwargs.pop("types"))
            difference = self.accepted_cards - VALID_CARDS
            if difference:
                raise ImproperlyConfigured(
                    "The following accepted_cards are unknown: %s" % difference
                )

        _kwargs.update(kwargs)
        super().__init__(*args, **_kwargs)

    def clean(self, value):
        """
        Check if given CC number is valid and one of the
        card types we accept
        """
        non_decimal = re.compile(r"\D+")
        value = non_decimal.sub("", (value or "").strip())

        if value and not bankcards.luhn(value):
            raise forms.ValidationError("Пожалуйста введите действующий номер карты.")

        if hasattr(self, "accepted_cards"):
            card_type = bankcards.bankcard_type(value)
            if card_type not in self.accepted_cards:
                raise forms.ValidationError("%s карты не принимаются." % card_type)

        return super().clean(value)


class BankcardMonthWidget(forms.MultiWidget):
    """
    Widget containing two select boxes for selecting the month and year
    """

    def decompress(self, value):
        return [value.month, value.year] if value else [None, None]

    def format_output(self, rendered_widgets):
        html = " ".join(rendered_widgets)
        return '<span style="white-space: nowrap">%s</span>' % html


# pylint: disable=W0223
class BankcardMonthField(forms.MultiValueField):
    """
    A modified version of the snippet: http://djangosnippets.org/snippets/907/
    """

    default_error_messages = {
        "invalid_month": "Введите действительный месяц.",
        "invalid_year": "Введите действительный год.",
    }
    num_years = 5

    def __init__(self, *args, **kwargs):
        # Allow the number of years to be specified
        if "num_years" in kwargs:
            self.num_years = kwargs.pop("num_years")

        errors = self.default_error_messages.copy()
        if "error_messages" in kwargs:
            errors.update(kwargs["error_messages"])

        fields = (
            forms.ChoiceField(
                choices=self.month_choices(),
                error_messages={"invalid": errors["invalid_month"]},
            ),
            forms.ChoiceField(
                choices=self.year_choices(),
                error_messages={"invalid": errors["invalid_year"]},
            ),
        )
        if "widget" not in kwargs:
            kwargs["widget"] = BankcardMonthWidget(
                widgets=[fields[0].widget, fields[1].widget]
            )
        super().__init__(fields, *args, **kwargs)

    def month_choices(self):
        return []

    def year_choices(self):
        return []


class BankcardExpiryMonthField(BankcardMonthField):
    num_years = 10

    def __init__(self, *args, **kwargs):
        today = date.today()
        _kwargs = {
            "required": True,
            "label": "Действителен до",
            "initial": ["%.2d" % today.month, today.year],
        }
        _kwargs.update(kwargs)
        super().__init__(*args, **_kwargs)

    def month_choices(self):
        return [("%.2d" % x, "%.2d" % x) for x in range(1, 13)]

    def year_choices(self):
        return [
            (x, x) for x in range(date.today().year, date.today().year + self.num_years)
        ]

    def clean(self, value):
        expiry_date = super().clean(value)
        if expiry_date and date.today() > expiry_date:
            raise forms.ValidationError(
                "Введенная вами дата истечения срока действия уже прошла."
            )

        return expiry_date

    def compress(self, data_list):
        if data_list:
            if data_list[1] in validators.EMPTY_VALUES:
                error = self.error_messages["invalid_year"]
                raise forms.ValidationError(error)
            if data_list[0] in validators.EMPTY_VALUES:
                error = self.error_messages["invalid_month"]
                raise forms.ValidationError(error)
            year = int(data_list[1])
            month = int(data_list[0])
            # find last day of the month
            day = monthrange(year, month)[1]
            return date(year, month, day)
        return None


class BankcardStartingMonthField(BankcardMonthField):
    def __init__(self, *args, **kwargs):
        _kwargs = {
            "required": False,
            "label": "Действителен с",
        }
        _kwargs.update(kwargs)
        super().__init__(*args, **_kwargs)

    def month_choices(self):
        months = [("%.2d" % x, "%.2d" % x) for x in range(1, 13)]
        months.insert(0, ("", "--"))
        return months

    def year_choices(self):
        today = date.today()
        years = [(x, x) for x in range(today.year - self.num_years, today.year + 1)]
        years.insert(0, ("", "--"))
        return years

    def clean(self, value):
        starting_date = super().clean(value)
        if starting_date and date.today() < starting_date:
            raise forms.ValidationError(
                "Введенная вами дата начала находится в будущем."
            )
        return starting_date

    def compress(self, data_list):
        if data_list:
            if data_list[1] in validators.EMPTY_VALUES:
                error = self.error_messages["invalid_year"]
                raise forms.ValidationError(error)
            if data_list[0] in validators.EMPTY_VALUES:
                error = self.error_messages["invalid_month"]
                raise forms.ValidationError(error)
            year = int(data_list[1])
            month = int(data_list[0])
            return date(year, month, 1)
        return None


class BankcardCCVField(forms.RegexField):
    def __init__(self, *args, **kwargs):
        _kwargs = {
            "required": True,
            "label": "CCV",
            "widget": forms.TextInput(attrs={"size": "5"}),
            "error_messages": {"invalid": "Пожалуйста, введите 4-значный номер"},
            "help_text": "Это четырехзначный код безопасности на обратной стороне банковской карты",
        }
        _kwargs.update(kwargs)
        super().__init__(r"^\d{3,4}$", *args, **_kwargs)

    def clean(self, value):
        if value is not None:
            value = value.strip()
        return super().clean(value)


class BankcardForm(forms.ModelForm):
    # By default, this number field will accept any number. The only validation
    # is whether it passes the luhn check. If you wish to only accept certain
    # types of card, you can pass a types kwarg to BankcardNumberField, e.g.
    #
    # BankcardNumberField(types=[bankcards.VISA, bankcards.VISA_ELECTRON,])

    number = BankcardNumberField()
    ccv = BankcardCCVField()
    start_month = BankcardStartingMonthField()
    expiry_month = BankcardExpiryMonthField()

    class Meta:
        model = Bankcard
        fields = ("number", "start_month", "expiry_month", "ccv")

    def clean(self):
        data = self.cleaned_data
        number, ccv = data.get("number"), data.get("ccv")
        if number and ccv:
            if bankcards.is_amex(number) and len(ccv) != 4:
                raise forms.ValidationError(
                    "Карты American Express используют 4-значный код безопасности"
                )

        return data

    def save(self, *args, **kwargs):
        # It doesn't really make sense to save directly from the form as saving
        # will obfuscate some of the card details which you normally need to
        # pass to a payment gateway.  Better to use the bankcard property below
        # to get the cleaned up data, then once you've used the sensitive
        # details, you can save.
        raise RuntimeError("Don't save bankcards directly from form")

    @property
    def bankcard(self):
        """
        Return an instance of the Bankcard model (unsaved)
        """
        return Bankcard(
            number=self.cleaned_data["number"],
            expiry_date=self.cleaned_data["expiry_month"],
            start_date=self.cleaned_data["start_month"],
            ccv=self.cleaned_data["ccv"],
        )
