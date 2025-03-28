from core.loading import get_model
from django.contrib import admin

Line = get_model("basket", "line")
LineAttribute = get_model("basket", "LineAttribute")
Basket = get_model("basket", "Basket")


class LineInline(admin.TabularInline):
    model = Line
    readonly_fields = (
        "line_reference",
        "product",
        "tax_code",
        "price_currency",
        "stockrecord",
    )


class LineAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "basket",
        "product",
        "stockrecord",
        "quantity",
        "tax_code",
        "price_currency",
        "date_created",
    )
    readonly_fields = (
        "basket",
        "stockrecord",
        "line_reference",
        "product",
        "price_currency",
        "quantity",
    )


class BasketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "status",
        "num_lines",
        "contains_a_voucher",
        "date_created",
        "date_submitted",
        "time_before_submit",
    )
    readonly_fields = ("owner", "date_merged", "date_submitted")
    inlines = [LineInline]


admin.site.register(Basket, BasketAdmin)
admin.site.register(Line, LineAdmin)
admin.site.register(LineAttribute)
