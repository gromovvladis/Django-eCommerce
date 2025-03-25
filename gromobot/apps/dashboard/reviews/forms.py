from core.forms.widgets import DatePickerInput
from core.loading import get_model
from django import forms

ProductReview = get_model("product_reviews", "ProductReview")
OrderReview = get_model("order_reviews", "OrderReview")


class DashboardProductReviewForm(forms.ModelForm):
    choices = (
        (ProductReview.HELPFUL, "Полезный"),
        (ProductReview.UNHELPFUL, "Неполезный"),
    )
    status = forms.ChoiceField(choices=choices, label="Статус")

    class Meta:
        model = ProductReview
        fields = ("status",)


class DashboardOrderReviewForm(forms.ModelForm):
    choices = (
        (ProductReview.HELPFUL, "Полезный"),
        (ProductReview.UNHELPFUL, "Неполезный"),
    )
    status = forms.ChoiceField(choices=choices, label="Статус")

    class Meta:
        model = OrderReview
        fields = ("status",)


class ProductReviewSearchForm(forms.Form):
    STATUS_CHOICES = (("", "------------"),) + ProductReview.STATUS_CHOICES
    keyword = forms.CharField(required=False, label="Ключевое слово")
    username = forms.CharField(
        required=False,
        label="Телефон Клиента",
        widget=forms.TextInput(
            attrs={
                "placeholder": "+7 (900) 000-0000",
            }
        ),
    )
    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES, label="Статус")
    date_from = forms.DateTimeField(
        required=False, label="Дата с", widget=DatePickerInput
    )
    date_to = forms.DateTimeField(
        required=False, label="Дата до", widget=DatePickerInput
    )

    def get_friendly_status(self):
        raw = int(self.cleaned_data["status"])
        for key, value in self.STATUS_CHOICES:
            if key == raw:
                return value
        return ""
