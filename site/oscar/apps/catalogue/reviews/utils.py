from django.conf import settings

from oscar.core.loading import get_model


def get_default_review_status():
    ProductReview = get_model("reviews", "ProductReview")
    return ProductReview.APPROVED
