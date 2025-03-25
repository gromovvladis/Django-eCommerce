from core.loading import get_model
from django.contrib import admin

OrderReview = get_model("order_reviews", "OrderReview")

admin.site.register(OrderReview)

