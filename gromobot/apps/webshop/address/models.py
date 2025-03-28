from core.compat import AUTH_USER_MODEL
from django.db import models


class Address(models.Model):
    """
    Superclass address object

    This is subclassed and extended to provide models for
    user, shipping addresses.
    """

    # We use quite a few lines of an address as they are often quite long and
    # it's easier to just hide the unnecessary ones than add extra ones.
    line1 = models.CharField("Улица, дом", max_length=255, blank=True, null=True)
    line2 = models.PositiveIntegerField("Квартира", blank=True, null=True)
    line3 = models.PositiveIntegerField("Подъезд", blank=True, null=True)
    line4 = models.PositiveIntegerField("Этаж", blank=True, null=True)

    coords_long = models.CharField(
        "Координаты долгота", max_length=255, blank=True, null=True
    )
    coords_lat = models.CharField(
        "Координаты широта", max_length=255, blank=True, null=True
    )

    # A field only used for searching addresses - this contains all the
    # `search_fields`.  This is effectively a poor man's Solr text field.
    search_text = models.TextField(
        "Адрес для поиска. Используется только для поиска", editable=False
    )

    # Fields, used for `summary` property definition and hash generation.
    search_fields = base_fields = (
        "line1",
        "line2",
        "line3",
        "line4",
    )
    address_fields = (
        ("line1", line1.verbose_name),
        ("line2", line2.verbose_name),
        ("line3", line3.verbose_name),
        ("line4", line4.verbose_name),
    )

    def __str__(self):
        return self.summary

    class Meta:
        verbose_name = "Адрес"
        verbose_name_plural = "Адреса"

    # Saving

    def save(self, *args, **kwargs):
        self._update_search_text()
        super().save(*args, **kwargs)

    def clean(self):
        # Strip all whitespace
        for field in [
            "line1",
            "line2",
            "line3",
            "line4",
        ]:
            if self.__dict__[field]:
                if isinstance(self.__dict__[field], str):
                    self.__dict__[field] = self.__dict__[field].strip()

    def _update_search_text(self):
        self.search_text = " ".join(
            filter(None, [str(getattr(self, field)) for field in self.search_fields])
        )

    # Properties

    @property
    def summary(self):
        """
        Returns a single string summary of the address,
        separating fields using commas.
        """
        return ", ".join(self.active_address_fields())

    # Helpers

    def get_field_values(self, fields):
        field_values = []
        for field in fields:
            value = getattr(self, field)
            if value is not None:
                field_values.append(str(value))
        return field_values

    def populate_alternative_model(self, address_model):
        """
        For populating an address model using the matching fields
        from this one.

        This is used to convert a user address to a shipping address
        as part of the checkout process.
        """
        destination_field_names = [field.name for field in address_model._meta.fields]
        for field_name in [field.name for field in self._meta.fields]:
            if field_name in destination_field_names and field_name != "id":
                setattr(address_model, field_name, getattr(self, field_name))

    def active_address_fields(self):
        return [
            str(val)
            for val in [getattr(self, field) for field in self.search_fields]
            if val is not None
        ]

    def active_address_fields_and_labels(self):
        return [
            {"label": label, "value": str(getattr(self, field))}
            for field, label in self.address_fields
            if getattr(self, field)
        ]


class StoreAddress(Address):
    """
    A store can have one or more addresses. This can be useful e.g. when
    determining US which depends on the origin of the shipment.
    """

    store = models.OneToOneField(
        "store.Store",
        on_delete=models.CASCADE,
        related_name="address",
        verbose_name="Магазин",
    )

    class Meta:
        app_label = "store"
        verbose_name = "Адрес магазина"
        verbose_name_plural = "Адреса магазинов"

    def save(self, *args, **kwargs):
        if self.line1:
            super().save(*args, **kwargs)
        else:
            if self.pk:
                self.delete()


class ShippingAddress(Address):
    """
    A shipping address.

    A shipping address should not be edited once the order has been placed -
    it should be read-only after that.

    NOTE:
    ShippingAddress is a model of the order app. But moving it there is tricky
    due to circular import issues that are amplified by get_model/get_class
    calls pre-Django 1.7 to register receivers. So...
    TODO: Once Django 1.6 support is dropped, move BillingAddress and
    ShippingAddress to the order app, and move
    StoreAddress to the store app.
    """

    notes = models.TextField(
        blank=True,
        verbose_name="Комментарий курьеру",
        help_text="Комментарий курьеру по поводу адреса доставки",
    )

    note_field = [
        ("notes", notes.verbose_name),
    ]

    def note_field_and_label(self):
        """
        Returns the non-empty components of the address, but merging the
        title, first_name and last_name into a single line. It uses fields
        listed out in `base_fields` property.
        """
        field_values = []
        label = self.note_field[1]
        value = str(getattr(self, self.note_field[0]))
        if isinstance(value, str):
            value.strip()
        field_values.append({"label": label, "value": value})
        return field_values

    class Meta:
        # ShippingAddress is registered in order/models.py
        app_label = "order"
        verbose_name = "Адрес доставки"
        verbose_name_plural = "Адреса доставки"

    @property
    def order(self):
        """
        Return the order linked to this shipping address
        """
        return self.order_set.first()


class UserAddress(ShippingAddress):
    """
    A user's address.  A user can have many of these and together they form an
    'address book' of sorts for the user.

    We use a separate model for shipping (even though there will be
    some data duplication) because we don't want shipping addresses
    changed or deleted once an order has been placed.  By having a separate
    model, we allow users the ability to add/edit/delete from their address
    book without affecting orders already placed.
    """

    user = models.OneToOneField(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="address",
        verbose_name="Пользователь",
    )

    date_created = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        app_label = "address"
        verbose_name = "Адрес пользователя"
        verbose_name_plural = "Адреса пользователей"
