import factory
from core.loading import get_model

__all__ = ["WishListFactory"]


class WishListFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Wishlist %d" % n)

    class Meta:
        model = get_model("wishlists", "WishList")
