from django import forms
from django.db import transaction
from django.urls import reverse
from django.utils.safestring import mark_safe
from apps.webshop.voucher.utils import get_unused_code
from core.loading import get_model
from core.forms import widgets

Voucher = get_model("voucher", "Voucher")
VoucherSet = get_model("voucher", "VoucherSet")
ConditionalOffer = get_model("offer", "ConditionalOffer")


class VoucherForm(forms.ModelForm):
    """
    A specialised form for creating a voucher model, and capturing the offers
    that apply to it.
    """

    offers = forms.ModelMultipleChoiceField(
        label="Какие предложения действительны для этого ваучера?",
        queryset=ConditionalOffer.objects.filter(offer_type=ConditionalOffer.VOUCHER),
    )

    class Meta:
        model = Voucher
        fields = [
            "name",
            "code",
            "start_datetime",
            "end_datetime",
            "usage",
        ]
        widgets = {
            "start_datetime": widgets.DateTimePickerInput(),
            "end_datetime": widgets.DateTimePickerInput(),
        }

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()


class VoucherSearchForm(forms.Form):
    name = forms.CharField(required=False, label="Имя")
    code = forms.CharField(required=False, label="Код")
    offer_name = forms.CharField(required=False, label="Название предложения")
    is_active = forms.NullBooleanField(
        required=False, label="Активен?", widget=widgets.NullBooleanSelect
    )
    in_set = forms.NullBooleanField(
        required=False, label="В наборе ваучеров?", widget=widgets.NullBooleanSelect
    )
    has_offers = forms.NullBooleanField(
        required=False, label="Есть предложения?", widget=widgets.NullBooleanSelect
    )

    basic_fields = [
        "name",
        "code",
        "is_active",
        "in_set",
    ]

    def clean_code(self):
        return self.cleaned_data["code"].upper()


class VoucherSetForm(forms.ModelForm):
    usage = forms.ChoiceField(
        choices=(("", "---------"),) + Voucher.USAGE_CHOICES, label="Использование"
    )

    offers = forms.ModelMultipleChoiceField(
        label="Какие предложения действительны для этого набора ваучеров?",
        queryset=ConditionalOffer.objects.filter(offer_type=ConditionalOffer.VOUCHER),
    )

    class Meta:
        model = VoucherSet
        fields = [
            "name",
            "code_length",
            "description",
            "start_datetime",
            "end_datetime",
            "count",
        ]
        widgets = {
            "start_datetime": widgets.DateTimePickerInput(),
            "end_datetime": widgets.DateTimePickerInput(),
        }

    def clean_count(self):
        data = self.cleaned_data["count"]
        if (self.instance.pk is not None) and (data < self.instance.count):
            detail_url = reverse(
                "dashboard:voucher-set-detail", kwargs={"pk": self.instance.pk}
            )
            raise forms.ValidationError(
                mark_safe(
                    "Это нельзя использовать для удаления ваучеров (в настоящее время %s) в этом наборе. "
                    "Это можно сделать на странице <a href='%s'>Поднобности</a>."
                    % (self.instance.count, detail_url)
                )
            )
        return data

    @transaction.atomic
    def save(self, commit=True):
        instance = super().save(commit)
        if commit:
            usage = self.cleaned_data["usage"]
            offers = self.cleaned_data["offers"]
            if instance is not None:
                # Update vouchers in this set
                for i, voucher in enumerate(instance.vouchers.order_by("date_created")):
                    voucher.name = "%s - %d" % (instance.name, i + 1)
                    voucher.usage = usage
                    voucher.start_datetime = instance.start_datetime
                    voucher.end_datetime = instance.end_datetime
                    voucher.save()
                    voucher.offers.set(offers)
            # Add vouchers to this set
            vouchers_added = False
            for i in range(instance.vouchers.count(), instance.count):
                voucher = Voucher.objects.create(
                    name="%s - %d" % (instance.name, i + 1),
                    code=get_unused_code(length=instance.code_length),
                    voucher_set=instance,
                    usage=usage,
                    start_datetime=instance.start_datetime,
                    end_datetime=instance.end_datetime,
                )
                voucher.offers.add(*offers)
                vouchers_added = True
            if vouchers_added:
                instance.update_count()
        return instance


class VoucherSetSearchForm(forms.Form):
    code = forms.CharField(required=False, label="Код")

    def clean_code(self):
        return self.cleaned_data["code"].upper()
