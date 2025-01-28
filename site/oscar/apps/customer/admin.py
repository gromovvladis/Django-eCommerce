from django.contrib import admin

from oscar.core.loading import get_model

OrderReview = get_model("customer", "OrderReview")

admin.site.register(OrderReview)