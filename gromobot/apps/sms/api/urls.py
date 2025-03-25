from django.urls import path

from .views import AuthAPIView, ChangePhoneNumberAPIView, EntryAPIView

urlpatterns = [
    path("sign-in/", EntryAPIView.as_view()),
    path("auth/", AuthAPIView.as_view()),
    path("change-phonenumber/", ChangePhoneNumberAPIView.as_view()),
]
