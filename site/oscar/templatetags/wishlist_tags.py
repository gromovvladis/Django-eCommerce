from django import template

register = template.Library()


@register.simple_tag
def wishlists_containing_product(wishlist, product):
    if not wishlist:
        return False
    
    return wishlist.is_have_this_product(product)

@register.simple_tag
def get_host(reqest):
    return reqest._current_scheme_host