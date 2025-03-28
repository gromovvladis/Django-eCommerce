from django.urls import include, path

from .views import BandCreateView, BandDeleteView, BandListView, BandUpdateView

dashboard_urlpatterns = [
    path("band/create/", BandCreateView.as_view(), name="webshop-band-create"),
    path("band/", BandListView.as_view(), name="webshop-band-list"),
    # The RelatedFieldWidgetWrapper code does something funny with placeholder
    # urls, so it does need to match more than just a pk
    path("band/<str:pk>/update/", BandUpdateView.as_view(), name="webshop-band-update"),
    # The RelatedFieldWidgetWrapper code does something funny with placeholder
    # urls, so it does need to match more than just a pk
    path("band/<str:pk>/delete/", BandDeleteView.as_view(), name="webshop-band-delete"),
]

urlpatterns = [
    path(
        "dashboard/",
        include((dashboard_urlpatterns, "dashboard"), namespace="dashboard"),
    ),
]
