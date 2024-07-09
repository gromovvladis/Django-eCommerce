from django import template

register = template.Library()


@register.simple_tag
def shipping_charge(method, basket, zonaId=None):
    """
    Template tag for calculating the shipping charge for a given shipping
    method and basket, and injecting it into the template context.
    """
    return method.calculate(basket, zonaId)


@register.simple_tag
def shipping_charge_discount(method, basket):
    """
    Template tag for calculating the shipping discount for a given shipping
    method and basket, and injecting it into the template context.
    """
    return method.discount(basket)


@register.simple_tag
def shipping_charge_excl_discount(method, basket, zonaId):
    """
    Template tag for calculating the shipping charge (excluding discounts) for
    a given shipping method and basket, and injecting it into the template
    context.
    """
    return method.calculate_excl_discount(basket, zonaId)

@register.simple_tag
def order_totals_and_shipping(basket, shipping_charge):
    """
    Template tag for calculating the shipping charge for a given shipping
    method and basket, and injecting it into the template context.
    """
    return basket.total + shipping_charge