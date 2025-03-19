from django.contrib import admin
from core.loading import get_model

admin.site.register(get_model("shipping", "ShippingZona"))
