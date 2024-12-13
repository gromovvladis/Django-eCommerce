from django.contrib import admin
from oscar.core.loading import get_model

CRMEvent = get_model("crm", "CRMEvent")
CRMBulk = get_model("crm", "CRMBulk")

class CRMEventAdmin(admin.ModelAdmin):
    date_hierarchy = "date_created"
    list_display = (
        "sender",
        "event_type",
        "body",
        "date_created",
    )
    search_fields = ["body"]

admin.site.register(CRMEvent, CRMEventAdmin)
admin.site.register(CRMBulk)
