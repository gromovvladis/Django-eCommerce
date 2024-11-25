from django.conf import settings

def metadata(request):
    """
    Add some generally useful metadata to the template context
    """
    return {
        "homepage_url": settings.OSCAR_HOMEPAGE,
        "stores_select": settings.STORE_SELECT,
        # Fallback to old settings name for backwards compatibility
        "google_analytics_id": (
            getattr(settings, "GOOGLE_ANALYTICS_ID", None)
        ),
        "yandex_analytics_id": (
            getattr(settings, "YANDEX_ANALYTICS_ID", None)
        ),
    }
