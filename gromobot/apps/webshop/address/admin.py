from core.loading import get_model
from django.contrib import admin

UserAddress = get_model("address", "UserAddress")

admin.site.register(UserAddress)
