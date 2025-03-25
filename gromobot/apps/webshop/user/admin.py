from core.loading import get_model
from django.contrib import admin

User = get_model("user", "User")
Staff = get_model("user", "Staff")

admin.site.register(User)
admin.site.register(Staff)
