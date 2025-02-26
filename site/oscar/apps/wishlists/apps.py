from django.urls import path

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class WishlistsConfig(OscarConfig):
    label = "wishlists"
    name = "oscar.apps.wishlists" 
    verbose_name = "Избранное"
    namespace = "wishlists"
