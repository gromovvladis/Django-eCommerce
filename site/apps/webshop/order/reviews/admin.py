from django.contrib import admin
from core.loading import get_model

OrderReview = get_model("order_reviews", "OrderReview")

admin.site.register(OrderReview)

