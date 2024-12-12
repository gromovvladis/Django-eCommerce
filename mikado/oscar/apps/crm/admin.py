from django.contrib import admin
from oscar.core.loading import get_model

CRMEvent = get_model("crm", "CRMEvent")
CRMBulk = get_model("crm", "CRMBulk")

admin.site.register(CRMEvent)
admin.site.register(CRMBulk)
