from django.contrib import admin
from oscar.core.loading import get_model

Action = get_model("home", "Action")
PromoCategory = get_model("home", "PromoCategory")

admin.site.register(Action)
admin.site.register(PromoCategory)
