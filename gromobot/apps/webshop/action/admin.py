from core.loading import get_model
from django.contrib import admin

Action = get_model("action", "Action")
ActionProduct = get_model("action", "ActionProduct")
PromoCategory = get_model("action", "PromoCategory")
PromoCategoryProduct = get_model("action", "PromoCategoryProduct")

admin.site.register(Action)
admin.site.register(ActionProduct)
admin.site.register(PromoCategory)
admin.site.register(PromoCategoryProduct)
