from core.loading import get_model
from django.contrib import admin

Action = get_model("action", "Action")
PromoCategory = get_model("action", "PromoCategory")

admin.site.register(Action)
admin.site.register(PromoCategory)
