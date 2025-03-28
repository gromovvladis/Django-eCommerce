from core.loading import get_model
from django.contrib import admin

Action = get_model("action", "Action")
ActionProduct = get_model("action", "ActionProduct")
PromoCategory = get_model("action", "PromoCategory")
PromoCategoryProduct = get_model("action", "PromoCategoryProduct")


class ActionProductInline(admin.TabularInline):
    model = ActionProduct
    extra = 3


class ActionAdmin(admin.ModelAdmin):
    inlines = [
        ActionProductInline,
    ]


class PromoCategoryProductInline(admin.TabularInline):
    model = PromoCategoryProduct
    extra = 3


class PromoCategoryAdmin(admin.ModelAdmin):
    inlines = [
        PromoCategoryProductInline,
    ]


admin.site.register(Action, ActionAdmin)
admin.site.register(PromoCategory, PromoCategoryAdmin)
