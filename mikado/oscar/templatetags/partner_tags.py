from django import template
from django.conf import settings
from django.core.cache import cache
from oscar.core.loading import get_model

Partner = get_model("partner", "Partner")
register = template.Library()

partner_default = settings.PARTNER_DEFAULT

@register.simple_tag
def selected_partner(request):   
    try:
        partners_select = cache.get('partners_select')

        if not partners_select:
            partners_select = Partner.objects.prefetch_related("addresses").filter(is_active=True)
            cache.set("partners_select", partners_select, 21600)  # Кэш на 6 часов

        if partners_select:
            partner_id = partner_default
            partner_basket = request.basket.partner_id
            partner_cookies = request.COOKIES.get("partner")

            if partner_basket is not None:
                partner_id = partner_basket
            elif partner_cookies is not None:
                partner_id = partner_cookies

            return Partner.objects.get(id=partner_id)

        return None

    except Partner.DoesNotExist:
        return None
