from django.contrib import admin
from oscar.core.loading import get_model

CRMEvent = get_model("crm", "CRMEvent")

admin.site.register(CRMEvent)
