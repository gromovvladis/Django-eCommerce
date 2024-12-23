from django.conf import settings

def metadata(request):
    """
    Add some generally useful metadata to the template context
    """
    return {
        "homepage_url": settings.OSCAR_HOMEPAGE,
        "primary_title": settings.PRIMARY_TITLE,
        "stores_select": settings.STORE_SELECT,
        "delivety_available": settings.DELIVERY_AVAILABLE,
        "support_link": settings.SUPPORT_LINK,
        # Fallback to old settings name for backwards compatibility
        "google_analytics_id": (
            getattr(settings, "GOOGLE_ANALYTICS_ID", None)
        ),
        "yandex_analytics_id": (
            getattr(settings, "YANDEX_ANALYTICS_ID", None)
        ),
    }
