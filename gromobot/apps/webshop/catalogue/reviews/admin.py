from core.loading import get_model
from django.contrib import admin

ProductReview = get_model("product_reviews", "ProductReview")


class ProductReviewAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "score",
        "status",
        "date_created",
    )


admin.site.register(ProductReview, ProductReviewAdmin)
