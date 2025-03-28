from core.loading import get_model
from django.contrib import admin

WishList = get_model("wishlists", "WishList")
Line = get_model("wishlists", "Line")


admin.site.register(WishList)
admin.site.register(Line)
