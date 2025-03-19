from django.contrib import admin
from core.loading import get_model

Store = get_model("store", "Store")
StockRecord = get_model("store", "StockRecord")


class StockRecordAdmin(admin.ModelAdmin):
    list_display = ("product", "store", "evotor_code", "price", "num_in_stock")
    list_filter = ("store",)


admin.site.register(Store)
admin.site.register(StockRecord, StockRecordAdmin)
