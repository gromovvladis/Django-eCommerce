from django.contrib import admin
from core.loading import get_model

EvotorEvent = get_model("evotor", "EvotorEvent")
EvotorBulk = get_model("evotor", "EvotorBulk")


class EvotorEventAdmin(admin.ModelAdmin):
    date_hierarchy = "date_created"
    list_display = (
        "sender",
        "event_type",
        "body",
        "date_created",
    )
    search_fields = ["body"]


admin.site.register(EvotorEvent, EvotorEventAdmin)
admin.site.register(EvotorBulk)
