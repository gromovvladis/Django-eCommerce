from django.contrib import admin
from oscar.core.loading import get_model

User = get_model("user", "User")
Staff = get_model("user", "Staff")

admin.site.register(User)
admin.site.register(Staff)
