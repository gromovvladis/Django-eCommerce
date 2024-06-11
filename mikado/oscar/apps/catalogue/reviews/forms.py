from django import forms
from oscar.core.loading import get_model

ProductReview = get_model("reviews", "ProductReview")
OrderReview = get_model("customer", "OrderReview")


class ProductReviewForm(forms.ModelForm):

    def __init__(self, product, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.product = product
        if user and user.is_authenticated:
            self.instance.user = user

    class Meta:
        model = ProductReview
        fields = ("score", "body")
        widgets = {
            'score': forms.RadioSelect(),
            'body': forms.Textarea(attrs={
                'class' : 'v-input v-input-textarea fill-width fill-height d-flex align-center v-input__padding pd-2',
                'rows': 6,
                'placeholder': "Ваш отзыв"
            }),
        }


class OrderReviewForm(forms.ModelForm):

    def __init__(self, order, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.order = order
        if user and user.is_authenticated:
            self.instance.user = user

    class Meta:
        model = OrderReview
        fields = ("score", "body")
        widgets = {
            'score': forms.RadioSelect(),
            'body': forms.Textarea(attrs={
                'class' : 'v-input v-input-textarea fill-width fill-height d-flex align-center v-input__padding pd-2',
                'rows': 6,
                'placeholder': "Ваш отзыв"
            }),
        }



class SortReviewsForm(forms.Form):
    SORT_BY_SCORE = "score"
    SORT_BY_RECENCY = "recency"
    SORT_REVIEWS_BY_CHOICES = (
        (SORT_BY_SCORE, "Оценка"),
        (SORT_BY_RECENCY, "Новизна"),
    )

    sort_by = forms.ChoiceField(
        choices=SORT_REVIEWS_BY_CHOICES,
        label="Сортировать по",
        initial=SORT_BY_SCORE,
        required=False,
    )
