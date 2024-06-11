from django import forms
from oscar.core.compat import get_user_model
from oscar.core.loading import get_model

# User = get_user_model()
# ProductAlert = get_model("customer", "ProductAlert")


class UserSearchForm(forms.Form):
    email = forms.CharField(required=False, label="Email")
    name = forms.CharField(required=False, label=("Имя пользователя", "Имя"))


# class ProductAlertUpdateForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         alert = kwargs["instance"]
#         if alert.user:
#             # Remove 'unconfirmed' from list of available choices when editing
#             # an alert for a real user
#             choices = self.fields["status"].choices
#             del choices[0]
#             self.fields["status"].choices = choices

#     class Meta:
#         model = ProductAlert
#         fields = [
#             "status",
#         ]


# class ProductAlertSearchForm(forms.Form):
#     STATUS_CHOICES = (("", "------------"),) + ProductAlert.STATUS_CHOICES

#     status = forms.ChoiceField(
#         required=False, choices=STATUS_CHOICES, label="Статус"
#     )
#     name = forms.CharField(required=False, label="Имя")
#     email = forms.EmailField(required=False, label="Email")
