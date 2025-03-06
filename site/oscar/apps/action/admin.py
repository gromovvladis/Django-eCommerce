from django.contrib import admin

from oscar.core.loading import get_model

Action = get_model("action", "Action")
PromoCategory = get_model("action", "PromoCategory")

admin.site.register(Action)
admin.site.register(PromoCategory)
