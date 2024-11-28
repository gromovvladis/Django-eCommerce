from django.db import models
from django.urls import reverse
from django.utils.crypto import get_random_string
from oscar.core.compat import AUTH_USER_MODEL


class WishList(models.Model):
    """
    Represents a user's wish lists of products.

    A user can have multiple wish lists, move products between them, etc.
    """

    # Only authenticated users can have wishlists
    owner = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name="wishlists",
        on_delete=models.CASCADE,
        verbose_name="Владелец",
    )
    # name = models.CharField(
    #     verbose_name="Имя", default="По умолчанию", max_length=255
    # )

    #: This key acts as primary key and is used instead of an int to make it
    #: harder to guess
    key = models.CharField(
        "Ключ", max_length=6, db_index=True, unique=True, editable=False
    )

    # Oscar core does not support public or shared wishlists at the moment, but
    # all the right hooks should be there
    # PUBLIC, PRIVATE, SHARED = ("Public", "Private", "Shared")
    # visibility = models.CharField(
    #     "Доступность", max_length=20, default=PUBLIC)

    # Convention: A user can have multiple wish lists. The last created wish
    # list for a user shall be their "default" wish list.
    # If an UI element only allows adding to wish list without
    # specifying which one , one shall use the default one.
    # That is a rare enough case to handle it by convention instead of a
    # BooleanField.
    date_created = models.DateTimeField(
        "Дата создания", auto_now_add=True, editable=False, db_index=True
    )

    def __str__(self):
        return "%s - Избранное" % (self.owner)

    def save(self, *args, **kwargs):
        if not self.pk or kwargs.get("force_insert", False):
            self.key = self.__class__.random_key()
        super().save(*args, **kwargs)

    @classmethod
    def random_key(cls, length=6):
        """
        Get a unique random generated key
        """
        while True:
            key = get_random_string(
                length=length, allowed_chars="abcdefghijklmnopqrstuvwxyz0123456789"
            )
            if not cls._default_manager.filter(key=key).exists():
                return key

    # def is_allowed_to_see(self, user):
    #     if user == self.owner:
    #         return True
    #     elif self.visibility == self.PUBLIC:
    #         return True
    #     elif self.visibility == self.SHARED and user.is_authenticated:
    #         return self.shared_emails.filter(email=user.email).exists()
    #     return False
    
    def is_have_this_product(self, product):
        if len(self.lines.filter(product=product)) != 0:
            return True
        return False

    def is_allowed_to_edit(self, user):
        # currently only the owner can edit their wish list
        return user == self.owner

    class Meta:
        app_label = "wishlists"
        ordering = (
            "owner",
            "date_created",
        )
        verbose_name = "Избранное"

    def get_absolute_url(self):
        # return reverse("customer:wishlist-detail", kwargs={"key": self.key})
        return reverse("customer:wishlist-detail")

    def add(self, product):
        """
        Add a product to this wishlist
        """
        lines = self.lines.filter(product=product)
        if len(lines) == 0:
            self.lines.create(product=product, name=product.get_name())
        # else:
        #     line = lines[0]
        #     line.quantity += 1
        #     line.save()

    def get_shared_url(self):
        return reverse("wishlists:detail", kwargs={"key": self.key})

    # @property
    # def is_shareable(self):
    #     return self.visibility in [self.PUBLIC, self.SHARED]


class Line(models.Model):
    """
    One entry in a wish list. Similar to order lines or basket lines.
    """

    wishlist = models.ForeignKey(
        "wishlists.WishList",
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name="Избранное",
    )
    product = models.ForeignKey(
        "catalogue.Product",
        verbose_name="товар",
        related_name="wishlists_lines",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    # quantity = models.PositiveIntegerField("Количество", default=1)
    #: Store the name in case product gets deleted
    name = models.CharField("Название товара", max_length=255)

    def __str__(self):
        # return "%sx %s on %s" % (self.quantity, self.name, self.wishlist.name)
        return "%s on %s" % (self.name, self.wishlist)

    def get_name(self):
        if self.product:
            return self.product.get_name()
        else:
            return self.name

    class Meta:
        app_label = "wishlists"
        # Enforce sorting by order of creation.
        ordering = ["pk"]
        unique_together = (("wishlist", "product"),)
        verbose_name = "Позиция избранного"

