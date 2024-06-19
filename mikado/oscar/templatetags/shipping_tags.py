from django import template

register = template.Library()


@register.simple_tag
def shipping_charge(method, basket):
    """
    Template tag for calculating the shipping charge for a given shipping
    method and basket, and injecting it into the template context.
    """
    return method.calculate(basket)


@register.simple_tag
def shipping_charge_discount(method, basket):
    """
    Template tag for calculating the shipping discount for a given shipping
    method and basket, and injecting it into the template context.
    """
    return method.discount(basket)


@register.simple_tag
def shipping_charge_excl_discount(method, basket):
    """
    Template tag for calculating the shipping charge (excluding discounts) for
    a given shipping method and basket, and injecting it into the template
    context.
    """
    return method.calculate_excl_discount(basket)

@register.simple_tag
def order_totals_and_shipping(basket, shipping_method):
    """
    Template tag for calculating the shipping charge for a given shipping
    method and basket, and injecting it into the template context.
    """
    basket_total = basket.total

    if shipping_method.code == 'self-pick-up':
        discount = basket_total * shipping_method.pickup_discount / 100
        basket_total -= discount

    return basket_total