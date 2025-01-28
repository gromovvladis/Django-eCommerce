from django import forms
from oscar.core.loading import get_class, get_model

ProductReview = get_model("reviews", "productreview")
DatePickerInput = get_class("oscar.forms.widgets", "DatePickerInput")


class DashboardProductReviewForm(forms.ModelForm):
    choices = (
        (ProductReview.HELPFUL, "Полезный"),
        (ProductReview.UNHELPFUL, "Неполезный"),
    )
    status = forms.ChoiceField(choices=choices, label="Статус")

    class Meta:
        model = ProductReview
        fields = ("body", "score", "status")


class ProductReviewSearchForm(forms.Form):
    STATUS_CHOICES = (("", "------------"),) + ProductReview.STATUS_CHOICES
    keyword = forms.CharField(required=False, label="Ключевое слово")
    status = forms.ChoiceField(
        required=False, choices=STATUS_CHOICES, label="Статус"
    )
    date_from = forms.DateTimeField(
        required=False, label="Дата с", widget=DatePickerInput
    )
    date_to = forms.DateTimeField(required=False, label="до", widget=DatePickerInput)
    name = forms.CharField(required=False, label="Имя Клиента")

    def get_friendly_status(self):
        raw = int(self.cleaned_data["status"])
        for key, value in self.STATUS_CHOICES:
            if key == raw:
                return value
        return ""
