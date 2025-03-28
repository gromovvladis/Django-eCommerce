from django import template

register = template.Library()


@register.simple_tag
def shipping_charge(shipping_method, basket, zonaId=None):
    """
    Template tag for calculating the shipping charge for a given shipping
    method and basket, and injecting it into the template context.
    """
    return shipping_method.calculate_from_zona_id(basket, zonaId)


@register.simple_tag
def shipping_charge_discount(shipping_method, basket):
    """
    Template tag for calculating the shipping discount for a given shipping
    method and basket, and injecting it into the template context.
    """
    return shipping_method.discount(basket)


@register.simple_tag
def shipping_charge_excl_discount(shipping_method, basket, zonaId):
    """
    Template tag for calculating the shipping charge (excluding discounts) for
    a given shipping method and basket, and injecting it into the template
    context.
    """
    return shipping_method.calculate_excl_discount(basket, zonaId)


@register.simple_tag
def order_totals_and_shipping(basket, shipping_charge):
    """
    Template tag for calculating the shipping charge for a given shipping
    method and basket, and injecting it into the template context.
    """
    if shipping_charge:
        return basket.total + shipping_charge

    return basket.total
