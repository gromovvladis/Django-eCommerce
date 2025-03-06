from django.contrib import admin

from oscar.core.loading import get_model

admin.site.register(get_model("delivery", "DeliveryZona"))
