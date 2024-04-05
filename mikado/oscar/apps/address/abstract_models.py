import re
import zlib

from django.conf import settings
from django.core import exceptions
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from phonenumber_field.modelfields import PhoneNumberField

from oscar.core.compat import AUTH_USER_MODEL
from oscar.models.fields import UppercaseCharField


class AbstractAddress(models.Model):
    """
    Superclass address object

    This is subclassed and extended to provide models for
    user, shipping and billing addresses.
    """

    MR, MISS, MRS, MS, DR = ("Mr", "Miss", "Mrs", "Ms", "Dr")
    TITLE_CHOICES = (
        (MR, _("Mr")),
        (MISS, _("Miss")),
        (MRS, _("Mrs")),
        (MS, _("Ms")),
        (DR, _("Dr")),
    )

    title = models.CharField(
        pgettext_lazy("Treatment Pronouns for the customer", "Title"),
        max_length=64,
        choices=TITLE_CHOICES,
        blank=True,
    )
    first_name = models.CharField(_("First name"), max_length=255, blank=True)
    last_name = models.CharField(_("Last name"), max_length=255, blank=True)

    # We use quite a few lines of an address as they are often quite long and
    # it's easier to just hide the unnecessary ones than add extra ones.
    line1 = models.CharField(_("First line of address"), max_length=255)
    line2 = models.CharField(_("Second line of address"), max_length=255, blank=True)
    line3 = models.CharField(_("Third line of address"), max_length=255, blank=True)
    line4 = models.CharField(_("City"), max_length=255, blank=True)

    # A field only used for searching addresses - this contains all the
    # `search_fields`.  This is effectively a poor man's Solr text field.
    search_text = models.TextField(
        _("Search text - used only for searching addresses"), editable=False
    )
    search_fields = [
        "first_name",
        "line1",
        "line2",
        "line3",
        "line4",
    ]

    # Fields, used for `summary` property definition and hash generation.
    base_fields = hash_fields = [
        "salutation",
        "line1",
        "line2",
        "line3",
        "line4",
    ]

    def __str__(self):
        return self.summary

    class Meta:
        abstract = True
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")

    # Saving

    def save(self, *args, **kwargs):
        self._update_search_text()
        super().save(*args, **kwargs)

    def clean(self):
        # Strip all whitespace
        for field in [
            "first_name",
            "line1",
            "line2",
            "line3",
            "line4",
        ]:
            if self.__dict__[field]:
                self.__dict__[field] = self.__dict__[field].strip()

        # Ensure postcodes are valid for country
        # self.ensure_postcode_is_valid_for_country()

    # def ensure_postcode_is_valid_for_country(self):
    #     """
    #     Validate postcode given the country
    #     """
    #     if not self.postcode and self.POSTCODE_REQUIRED and self.country_id:
    #         country_code = self.country.iso_3166_1_a2
    #         regex = self.POSTCODES_REGEX.get(country_code, None)
    #         if regex:
    #             msg = _("Addresses in %(country)s require a valid postcode") % {
    #                 "country": self.country
    #             }
    #             raise exceptions.ValidationError(msg)

    #     if self.postcode and self.country_id:
    #         # Ensure postcodes are always uppercase
    #         postcode = self.postcode.upper().replace(" ", "")
    #         country_code = self.country.iso_3166_1_a2
    #         regex = self.POSTCODES_REGEX.get(country_code, None)

    #         # Validate postcode against regex for the country if available
    #         if regex and not re.match(regex, postcode):
    #             msg = _("The postcode '%(postcode)s' is not valid for %(country)s") % {
    #                 "postcode": self.postcode,
    #                 "country": self.country,
    #             }
    #             raise exceptions.ValidationError({"postcode": [msg]})

    def _update_search_text(self):
        self.search_text = self.join_fields(self.search_fields, separator=" ")

    # Properties

    @property
    def city(self):
        # Common alias
        return self.line4

    @property
    def summary(self):
        """
        Returns a single string summary of the address,
        separating fields using commas.
        """
        return ", ".join(self.active_address_fields())

    @property
    def salutation(self):
        """
        Name (including title)
        """
        return self.join_fields(
            ("title", "first_name", "last_name"), separator=" "
        ).strip()

    @property
    def name(self):
        return self.first_name

    # Helpers

    def get_field_values(self, fields):
        field_values = []
        for field in fields:
            # Title is special case
            if field == "title":
                value = self.get_title_display()
            elif field == "salutation":
                value = self.salutation
            else:
                value = getattr(self, field)
            field_values.append(value)
        return field_values

    def get_address_field_values(self, fields):
        """
        Returns set of field values within the salutation and country.
        """
        field_values = [f.strip() for f in self.get_field_values(fields) if f]
        return field_values

    def generate_hash(self):
        """
        Returns a hash of the address, based on standard set of fields, listed
        out in `hash_fields` property.
        """
        field_values = self.get_address_field_values(self.hash_fields)
        # Python 2 and 3 generates CRC checksum in different ranges, so
        # in order to generate platform-independent value we apply
        # `& 0xffffffff` expression.
        return zlib.crc32(", ".join(field_values).upper().encode("UTF8")) & 0xFFFFFFFF

    def join_fields(self, fields, separator=", "):
        """
        Join a sequence of fields using the specified separator
        """
        field_values = self.get_field_values(fields)
        return separator.join(filter(bool, field_values))

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
        """
        Returns the non-empty components of the address, but merging the
        title, first_name and last_name into a single line. It uses fields
        listed out in `base_fields` property.
        """
        return self.get_address_field_values(self.base_fields)


class AbstractShippingAddress(AbstractAddress):
    """
    A shipping address.

    A shipping address should not be edited once the order has been placed -
    it should be read-only after that.

    NOTE:
    ShippingAddress is a model of the order app. But moving it there is tricky
    due to circular import issues that are amplified by get_model/get_class
    calls pre-Django 1.7 to register receivers. So...
    TODO: Once Django 1.6 support is dropped, move AbstractBillingAddress and
    AbstractShippingAddress to the order app, and move
    PartnerAddress to the partner app.
    """

    phone_number = PhoneNumberField(
        _("Phone number"),
        blank=True,
        help_text=_("In case we need to call you about your order"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Instructions"),
        help_text=_("Tell us anything we should know when delivering your order."),
    )

    class Meta:
        abstract = True
        # ShippingAddress is registered in order/models.py
        app_label = "order"
        verbose_name = _("Shipping address")
        verbose_name_plural = _("Shipping addresses")

    @property
    def order(self):
        """
        Return the order linked to this shipping address
        """
        return self.order_set.first()


class AbstractUserAddress(AbstractShippingAddress):
    """
    A user's address.  A user can have many of these and together they form an
    'address book' of sorts for the user.

    We use a separate model for shipping and billing (even though there will be
    some data duplication) because we don't want shipping/billing addresses
    changed or deleted once an order has been placed.  By having a separate
    model, we allow users the ability to add/edit/delete from their address
    book without affecting orders already placed.
    """

    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("User"),
    )

    #: Whether this address is the default for shipping
    is_default_for_shipping = models.BooleanField(
        _("Default shipping address?"), default=False
    )

    #: We keep track of the number of times an address has been used
    #: as a shipping address so we can show the most popular ones
    #: first at the checkout.
    num_orders_as_shipping_address = models.PositiveIntegerField(
        _("Number of Orders as Shipping Address"), default=0
    )

    #: A hash is kept to try and avoid duplicate addresses being added
    #: to the address book.
    hash = models.CharField(
        _("Address Hash"), max_length=255, db_index=True, editable=False
    )
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Save a hash of the address fields
        """
        # Save a hash of the address fields so we can check whether two
        # addresses are the same to avoid saving duplicates
        self.hash = self.generate_hash()

        # Ensure that each user only has one default shipping address
        # and billing address
        self._ensure_defaults_integrity()
        super().save(*args, **kwargs)

    def _ensure_defaults_integrity(self):
        if self.is_default_for_shipping:
            self.__class__._default_manager.filter(
                user=self.user, is_default_for_shipping=True
            ).update(is_default_for_shipping=False)

    class Meta:
        abstract = True
        app_label = "address"
        verbose_name = _("User address")
        verbose_name_plural = _("User addresses")
        ordering = ["-num_orders_as_shipping_address"]
        unique_together = ("user", "hash")

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude)
        qs = self.__class__.objects.filter(user=self.user, hash=self.generate_hash())
        if self.id:
            qs = qs.exclude(id=self.id)
        if qs.exists():
            raise exceptions.ValidationError(
                {"__all__": [_("This address is already in your address book")]}
            )


class AbstractPartnerAddress(AbstractAddress):
    """
    A partner can have one or more addresses. This can be useful e.g. when
    determining US tax which depends on the origin of the shipment.
    """

    partner = models.ForeignKey(
        "partner.Partner",
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("Partner"),
    )

    class Meta:
        abstract = True
        app_label = "partner"
        verbose_name = _("Partner address")
        verbose_name_plural = _("Partner addresses")
