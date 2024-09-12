from django.conf import settings
from django.core.cache import cache

from oscar.core.loading import get_model
Partner = get_model("partner", "Partner")

def metadata(request):
    """
    Add some generally useful metadata to the template context
    """
    if settings.PARTNER_SELECT:
        partners_select = cache.get('partners_select')
        if not partners_select:
            partners_select = Partner.objects.all()
            cache.set("partners_select", partners_select, 7200)
    else:
        partners_select = None

    return {
        "homepage_url": settings.OSCAR_HOMEPAGE,
        "partners_select": partners_select,
        # Fallback to old settings name for backwards compatibility
        "google_analytics_id": (
            getattr(settings, "GOOGLE_ANALYTICS_ID", None)
        ),
        "yandex_analytics_id": (
            getattr(settings, "YANDEX_ANALYTICS_ID", None)
        ),
    }
