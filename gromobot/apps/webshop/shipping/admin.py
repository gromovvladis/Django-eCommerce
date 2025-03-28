from core.loading import get_model
from django.contrib import admin

admin.site.register(get_model("shipping", "ShippingZona"))
