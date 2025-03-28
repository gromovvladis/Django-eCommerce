from django import template

register = template.Library()


@register.filter
def stars(review, stars):
    return int(stars) <= review.score


@register.filter
def is_review_permitted(product, user):
    return product and product.is_review_permitted(user)
