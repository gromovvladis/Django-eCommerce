from core.loading import get_model
from django.contrib import admin

ShippingZona = get_model("shipping", "ShippingZona")

admin.site.register(ShippingZona)
