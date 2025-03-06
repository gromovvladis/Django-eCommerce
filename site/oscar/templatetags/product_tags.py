import random
from django import template
from django.template.loader import select_template

register = template.Library()


@register.simple_tag(takes_context=True)
def render_product(context, product):
    """
    Render a product snippet as you would see in a browsing display.

    This templatetag looks for different templates depending on the article and
    product class of the passed product.  This allows alternative templates to
    be used for different product classes.
    """
    if not product:
        # Search index is returning products that don't exist in the
        # database...
        return ""

    names = [
        # "oscar/catalogue/partials/product/article-%s.html" % product.article,
        # "oscar/catalogue/partials/product/class-%s.html" % product.get_product_class().slug,
        "oscar/catalogue/partials/product.html",
    ]
    template_ = select_template(names)
    context = context.flatten()

    # Ensure the passed product is in the context as 'product'
    context["product"] = product
    range_start = 10 ** (5)
    range_finish = (10 ** 6) - 1
    context["unique_number"] = random.randint(range_start, range_finish)
    return template_.render(context)
