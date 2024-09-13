from django import template
from django.core.cache import cache
from oscar.core.loading import get_model

Partner = get_model("partner", "Partner")
register = template.Library()

@register.simple_tag
def selected_partner(request):   

    partners_select = cache.get('partners_select')
    if not partners_select:
        partners_select = Partner.objects.all()
        cache.set("partners_select", partners_select, 21600)

    partner_id = 1        
    partner_basket = request.basket.partner_id
    partner_cookies = request.COOKIES.get("partner", None)

    if partner_basket is not None:
        partner_id = partner_basket
    elif partner_cookies is not None:
        partner_id = partner_cookies

    return Partner.objects.get(id=partner_id) 
