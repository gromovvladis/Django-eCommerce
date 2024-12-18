from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from oscar.core.loading import get_model

OrderReview = get_model("customer", "OrderReview")

admin.site.register(OrderReview)