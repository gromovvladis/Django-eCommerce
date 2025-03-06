from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import views
from django.urls import include, path

from oscar.views import handler403, handler404, handler500
from oscar.apps.sitemaps import base_sitemaps

admin.autodiscover()

urlpatterns = [
    # Include admin as convenience. It's unsupported and only included
    # for developers.
    path("superadmin/", admin.site.urls),
    # include a basic sitemap
    path("sitemap.xml", views.index, {"sitemaps": base_sitemaps}),
    path(
        "sitemap-<slug:section>.xml",
        views.sitemap,
        {"sitemaps": base_sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]

# Prefix Oscar URLs
urlpatterns += [path("", include(apps.get_app_config("oscar").urls[0]))]

if settings.DEBUG:
    import debug_toolbar

    # Server statics and uploaded media
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Allow error pages to be tested
    urlpatterns += [
        path("403", handler403, {"exception": Exception()}),
        path("404", handler404, {"exception": Exception()}),
        path("500", handler500),
        path("__debug__/", include(debug_toolbar.urls)),
    ]
