import logging
import os
from datetime import date, datetime
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.finders import find
from django.core.cache import cache
from django.core.exceptions import (
    ImproperlyConfigured,
    ValidationError,
    ObjectDoesNotExist,
)
from django.core.files.base import File
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Count, Exists, OuterRef, Sum
from django.db.models.fields import Field
from django.db.models.lookups import StartsWith
from django.template.defaultfilters import striptags
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext, pgettext_lazy
from treebeard.mp_tree import MP_Node

from oscar.core.decorators import deprecated
from oscar.core.loading import get_class, get_classes, get_model
from oscar.core.utils import get_default_currency, slugify
from oscar.core.validators import non_python_keyword
from oscar.models.fields import AutoSlugField, NullCharField
from oscar.models.fields.slugfield import SlugField
from oscar.utils.models import get_image_upload_path







class AbstractAttributeOption(models.Model):
    """
    Provides an option within an option group for an attribute type
    Examples: In a Language group, English, Greek, French
    """

    group = models.ForeignKey(
        "catalogue.AttributeOptionGroup",
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name=_("Group"),
    )
    option = models.CharField(_("Option"), max_length=255)
    code = NullCharField(
        _("Unique identifier"),
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )

    def __str__(self):
        return self.option

    class Meta:
        abstract = True
        app_label = "catalogue"
        unique_together = ("group", "option")
        verbose_name = _("Attribute option")
        verbose_name_plural = _("Attribute options")


class AbstractOption(models.Model):
    """
    An option that can be selected for a particular item when the product
    is added to the basket.

    For example,  a list ID for an SMS message send, or a personalised message
    to print on a T-shirt.

    This is not the same as an 'attribute' as options do not have a fixed value
    for a particular item.  Instead, option need to be specified by a customer
    when they add the item to their basket.

    The `type` of the option determines the form input that will be used to
    collect the information from the customer, and the `required` attribute
    determines whether a value must be supplied in order to add the item to the basket.
    """

    # Option types
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"

    SELECT = "select"
    RADIO = "radio"
    MULTI_SELECT = "multi_select"
    CHECKBOX = "checkbox"

    TYPE_CHOICES = (
        (TEXT, _("Text")),
        (INTEGER, _("Integer")),
        (BOOLEAN, _("True / False")),
        (FLOAT, _("Float")),
        (DATE, _("Date")),
        (SELECT, _("Select")),
        (RADIO, _("Radio")),
        (MULTI_SELECT, _("Multi select")),
        (CHECKBOX, _("Checkbox")),
    )

    empty_label = "------"
    empty_radio_label = _("Skip this option")

    name = models.CharField(_("Name"), max_length=128, db_index=True)
    code = AutoSlugField(_("Code"), max_length=128, unique=True, populate_from="name")
    type = models.CharField(
        _("Type"), max_length=255, default=TEXT, choices=TYPE_CHOICES
    )
    required = models.BooleanField(_("Is this option required?"), default=False)

    help_text = models.CharField(
        verbose_name=_("Help text"),
        blank=True,
        null=True,
        max_length=255,
        help_text=_("Help text shown to the user on the add to basket form"),
    )
    order = models.IntegerField(
        _("Ordering"),
        null=True,
        blank=True,
        help_text=_("Controls the ordering of product options on product detail pages"),
        db_index=True,
    )
    option_group = models.ForeignKey(
        "catalogue.AttributeOptionGroup",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="product_options",
        verbose_name=_("Option Group"),
        help_text=_('Select an option group if using type "Option" or "Multi Option"'),
    )

    @property
    def is_option(self):
        return self.type in [self.SELECT, self.RADIO]

    @property
    def is_multi_option(self):
        return self.type in [self.MULTI_SELECT, self.CHECKBOX]

    @property
    def is_select(self):
        return self.type in [self.SELECT, self.MULTI_SELECT]

    @property
    def is_radio(self):
        return self.type in [self.RADIO]

    def add_empty_choice(self, choices):
        if self.is_select and not self.is_multi_option:
            choices = [("", self.empty_label)] + choices
        elif self.is_radio:
            choices = [(None, self.empty_radio_label)] + choices
        return choices

    def get_choices(self):
        if self.option_group:
            choices = [
                (opt.option, opt.option) for opt in self.option_group.options.all()
            ]
        else:
            choices = []

        if not self.required:
            choices = self.add_empty_choice(choices)

        return choices

    def clean(self):
        if self.type in [self.RADIO, self.SELECT, self.MULTI_SELECT, self.CHECKBOX]:
            if self.option_group is None:
                raise ValidationError(
                    _("Option Group is required for type %s") % self.get_type_display()
                )
        elif self.option_group:
            raise ValidationError(
                _("Option Group can not be used with type %s") % self.get_type_display()
            )
        return super().clean()

    class Meta:
        abstract = True
        app_label = "catalogue"
        ordering = ["order", "name"]
        verbose_name = _("Option")
        verbose_name_plural = _("Options")

    def __str__(self):
        return self.name







class AbstractVariantOption(models.Model):

    name = models.CharField(max_length=250,)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)

    variant_id = models.ForeignKey(
        "catalogue.Vatiant",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="product_variants",
        verbose_name=_("Variants"),
        help_text=_('Select an variants group if using type "variable"'),
    )

    price_currency = models.CharField(
        _("Currency"), max_length=12, default=get_default_currency
    )

    old_price = models.DecimalField(
        _("Old price"), 
        decimal_places=2,
        max_digits=12, 
        blank=True, 
        null=True,
        help_text=_('Show old price'),
    )

    price = models.DecimalField(
        _("Price"), 
        decimal_places=2,
        max_digits=12, 
        blank=False, 
        null=False,
        help_text=_('Show price'),
    )

    is_public = models.BooleanField(
        _("Is public"),
        default=True,
        db_index=True,
        help_text=_("Show this product in search results and catalogue listings."),
    )

    class Meta:
        app_label = "catalogue"
        verbose_name = _("Variant of product")
        verbose_name_plural = _("Variant of products")
        ordering = ("slug",)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        class_ = type(self)
        return f"<{class_.__module__}.{class_.__name__}(pk={self.pk!r}, name={self.name!r})>"

    @property
    def option_summary(self):
        options = [o.option for o in self.options.all()]
        return ", ".join(options)



class AbstractProductVariantGroup(models.Model):

    name = models.CharField(max_length=250,)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)

    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="product_variants",
        verbose_name=_("Product"),
        help_text=_('Select an variants group if using type "variable"'),
    )

    price_currency = models.CharField(
        _("Currency"), max_length=12, default=get_default_currency
    )

    old_price = models.DecimalField(
        _("Old price"), 
        decimal_places=2,
        max_digits=12, 
        blank=True, 
        null=True,
        help_text=_('Show old price'),
    )

    price = models.DecimalField(
        _("Price"), 
        decimal_places=2,
        max_digits=12, 
        blank=False, 
        null=False,
        help_text=_('Show price'),
    )

    is_public = models.BooleanField(
        _("Is public"),
        default=True,
        db_index=True,
        help_text=_("Show this product in search results and catalogue listings."),
    )

    time_to_make = models.IntegerField(
        _("Time"),
        default=60,
        db_index=True,
        help_text=_("Time to make the dich in minetes."),
    )

    upc = NullCharField(
        _("UPC"),
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        help_text=_(
            "Universal Product Code (UPC) is an identifier for "
            "a product which is not specific to a particular "
            " supplier. Eg an ISBN for a book."
        ),
    )

    #: Number of items in stock
    num_in_stock = models.PositiveIntegerField(
        _("Number in stock"), blank=True, null=True
    )

    #: The amount of stock allocated to orders but not fed back to the master
    #: stock system.  A typical stock update process will set the
    #: :py:attr:`.num_in_stock` variable to a new value and reset
    #: :py:attr:`.num_allocated` to zero.
    num_allocated = models.IntegerField(_("Number allocated"), blank=True, null=True)

    #: Threshold for low-stock alerts.  When stock goes beneath this threshold,
    #: an alert is triggered so warehouse managers can order more.
    low_stock_threshold = models.PositiveIntegerField(
        _("Low Stock Threshold"), blank=True, null=True
    )

    # Date information
    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("Date updated"), auto_now=True, db_index=True)

    def __str__(self):
        msg = "Partner: %s, product: %s" % (
            self.partner.display_name,
            self.product,
        )
        # if self.partner_sku:
        #     msg = "%s (%s)" % (msg, self.partner_sku)
        return msg

    class Meta:
        abstract = True
        app_label = "partner"
        # unique_together = ("partner", "partner_sku")
        verbose_name = _("Stock record")
        verbose_name_plural = _("Stock records")

    @property
    def net_stock_level(self):
        """
        The effective number in stock (e.g. available to buy).

        This is correct property to show the customer, not the
        :py:attr:`.num_in_stock` field as that doesn't account for allocations.
        This can be negative in some unusual circumstances
        """
        if self.num_in_stock is None:
            return 0
        if self.num_allocated is None:
            return self.num_in_stock
        return self.num_in_stock - self.num_allocated

    @cached_property
    def can_track_allocations(self):
        """Return True if the Product is set for stock tracking."""
        return self.product.get_product_class().track_stock

    # 2-stage stock management model

    def allocate(self, quantity):
        """
        Record a stock allocation.

        This normally happens when a product is bought at checkout.  When the
        product is actually shipped, then we 'consume' the allocation.

        """
        # Doesn't make sense to allocate if stock tracking is off.
        if not self.can_track_allocations:
            return

        # Send the pre-save signal
        self.pre_save_signal()

        # Atomic update
        (
            self.__class__.objects.filter(pk=self.pk).update(
                num_allocated=(Coalesce(F("num_allocated"), 0) + quantity)
            )
        )

        # Make sure the current object is up-to-date
        self.refresh_from_db(fields=["num_allocated"])

        # Send the post-save signal
        self.post_save_signal()

    allocate.alters_data = True

    def is_allocation_consumption_possible(self, quantity):
        """
        Test if a proposed stock consumption is permitted
        """
        return quantity <= min(self.num_allocated, self.num_in_stock)

    def consume_allocation(self, quantity):
        """
        Consume a previous allocation

        This is used when an item is shipped.  We remove the original
        allocation and adjust the number in stock accordingly
        """
        if not self.can_track_allocations:
            return
        if not self.is_allocation_consumption_possible(quantity):
            raise InvalidStockAdjustment(_("Invalid stock consumption request"))

        # send the pre save signal
        self.pre_save_signal()

        # Atomically consume allocations and stock
        (
            self.__class__.objects.filter(pk=self.pk).update(
                num_allocated=(Coalesce(F("num_allocated"), 0) - quantity),
                num_in_stock=(Coalesce(F("num_in_stock"), 0) - quantity),
            )
        )

        # Make sure current object is up-to-date
        self.refresh_from_db(fields=["num_allocated", "num_in_stock"])

        # Send the post-save signal
        self.post_save_signal()

    consume_allocation.alters_data = True

    def cancel_allocation(self, quantity):
        if not self.can_track_allocations:
            return

        # send the pre save signal
        self.pre_save_signal()

        # Atomically consume allocations
        (
            self.__class__.objects.filter(pk=self.pk).update(
                num_allocated=Coalesce(F("num_allocated"), 0)
                - Least(Coalesce(F("num_allocated"), 0), quantity),
            )
        )

        # Make sure current object is up-to-date
        self.refresh_from_db(fields=["num_allocated"])

        # Send the post-save signal
        self.post_save_signal()

    cancel_allocation.alters_data = True

    def pre_save_signal(self):
        signals.pre_save.send(
            sender=self.__class__,
            instance=self,
            created=False,
            raw=False,
            using=router.db_for_write(self.__class__, instance=self),
        )

    def post_save_signal(self):
        signals.post_save.send(
            sender=self.__class__,
            instance=self,
            created=False,
            raw=False,
            using=router.db_for_write(self.__class__, instance=self),
        )

    @property
    def is_below_threshold(self):
        if self.low_stock_threshold is None:
            return False
        return self.net_stock_level < self.low_stock_threshold




    class Meta:
        ordering = ("slug",)
        app_label = "catalogue"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        class_ = type(self)
        return f"<{class_.__module__}.{class_.__name__}(pk={self.pk!r}, name={self.name!r})>"

class AbstractProductVariant(models.Model):

    variant = models.CharField(max_length=250,)
    
    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="variantsgroup",
        verbose_name=_("Product"),
        help_text=_('Select an variants group if using type "variable"'),
    )

    product = models.ManyToManyField(
        "catalogue.Product",
        through="ProductAttributeValue",
        verbose_name=_("Products"),
        help_text=_(
            "product id"
        ),
    )

    product = models.ManyToManyField(
        "catalogue.Product",
        through="ProductAttributeValue",
        verbose_name=_("Products"),
        help_text=_(
            "product id"
        ),
    )


    class Meta:
        ordering = ("slug",)
        app_label = "catalogue"

    def __str__(self) -> str:
        return self.name






# это ок/   заголовок вариации
class AbstractVariant(models.Model):
    """
    Defines a Variants that collectively may be used as an
    attribute type

    For example, Language
    """

    name = models.CharField(_("Name"), max_length=128)
    code = NullCharField(
        _("Unique identifier"),
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        app_label = "catalogue"
        verbose_name = _("Variant group")
        verbose_name_plural = _("Variants group")

    # @property
    # def option_summary(self):
    #     options = [o.option for o in self.options.all()]
    #     return ", ".join(options)

# это ок/   значения вариации
class AbstractVariantValue(models.Model):
    """
    Provides an option within an variants group for an attribute type
    Examples: In a Language group, English, Greek, French
    """

    variants = models.ForeignKey(
        "catalogue.Variant",
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name=_("Group"),
    )

    option = models.CharField(_("Option"), max_length=255)
    
    code = NullCharField(
        _("Unique identifier"),
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )

    def __str__(self):
        return self.option

    class Meta:
        abstract = True
        app_label = "catalogue"
        unique_together = ("variants", "option")
        verbose_name = _("Attribute option")
        verbose_name_plural = _("Attribute options")

# это ок/   вариант продукты на основе вариаций выше
class AbstractProductVariant(models.Model):
    pass

class AbstractProductAttributeValue(models.Model):
    """
    The "through" model for the m2m relationship between :py:class:`Product <.AbstractProduct>` and
    :py:class:`ProductAttribute <.AbstractProductAttribute>`  This specifies the value of the attribute for
    a particular product

    For example: ``number_of_pages = 295``
    """

    attribute = models.ForeignKey(
        "catalogue.ProductAttribute",
        on_delete=models.CASCADE,
        verbose_name=_("Attribute"),
    )
    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="attribute_values",
        verbose_name=_("Product"),
    )

    value_text = models.TextField(_("Text"), blank=True, null=True)
    value_integer = models.IntegerField(
        _("Integer"), blank=True, null=True, db_index=True
    )
    value_boolean = models.BooleanField(
        _("Boolean"), blank=True, null=True, db_index=True
    )
    value_float = models.FloatField(_("Float"), blank=True, null=True, db_index=True)
    value_richtext = models.TextField(_("Richtext"), blank=True, null=True)
    value_date = models.DateField(_("Date"), blank=True, null=True, db_index=True)
    value_datetime = models.DateTimeField(
        _("DateTime"), blank=True, null=True, db_index=True
    )
    value_multi_option = models.ManyToManyField(
        "catalogue.AttributeOption",
        blank=True,
        related_name="multi_valued_attribute_values",
        verbose_name=_("Value multi option"),
    )
    value_option = models.ForeignKey(
        "catalogue.AttributeOption",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("Value option"),
    )
    value_file = models.FileField(
        upload_to=get_image_upload_path, max_length=255, blank=True, null=True
    )
    value_image = models.ImageField(
        upload_to=get_image_upload_path, max_length=255, blank=True, null=True
    )
    value_entity = GenericForeignKey("entity_content_type", "entity_object_id")

    entity_content_type = models.ForeignKey(
        ContentType, blank=True, editable=False, on_delete=models.CASCADE, null=True
    )
    entity_object_id = models.PositiveIntegerField(
        null=True, blank=True, editable=False
    )
    _dirty = False

    @cached_property
    def type(self):
        return self.attribute.type

    @property
    def value_field_name(self):
        return "value_%s" % self.type

    def _get_value(self):
        value = getattr(self, self.value_field_name)
        if hasattr(value, "all"):
            value = value.all()
        return value

    def _set_value(self, new_value):
        attr_name = self.value_field_name

        if self.attribute.is_option and isinstance(new_value, str):
            # Need to look up instance of AttributeOption
            new_value = self.attribute.option_group.options.get(option=new_value)
        elif self.attribute.is_multi_option:
            getattr(self, attr_name).set(new_value)
            self._dirty = True
            return

        setattr(self, attr_name, new_value)
        self._dirty = True
        return

    value = property(_get_value, _set_value)

    @property
    def is_dirty(self):
        return self._dirty

    class Meta:
        abstract = True
        app_label = "catalogue"
        unique_together = ("attribute", "product")
        verbose_name = _("Product attribute value")
        verbose_name_plural = _("Product attribute values")

    def __str__(self):
        return self.summary()

    def summary(self):
        """
        Gets a string representation of both the attribute and it's value,
        used e.g in product summaries.
        """
        return "%s: %s" % (self.attribute.name, self.value_as_text)

    @property
    def value_as_text(self):
        """
        Returns a string representation of the attribute's value. To customise
        e.g. image attribute values, declare a _image_as_text property and
        return something appropriate.
        """
        try:
            property_name = "_%s_as_text" % self.type
            return getattr(self, property_name, self.value)
        except ValueError:
            return ""

    @property
    def _multi_option_as_text(self):
        return ", ".join(str(option) for option in self.value_multi_option.all())

    @property
    def _option_as_text(self):
        return str(self.value_option)

    @property
    def _richtext_as_text(self):
        return strip_tags(self.value)

    @property
    def _entity_as_text(self):
        """
        Returns the unicode representation of the related model. You likely
        want to customise this (and maybe _entity_as_html) if you use entities.
        """
        return str(self.value)

    @property
    def _boolean_as_text(self):
        if self.value:
            return pgettext("Product attribute value", "Yes")
        return pgettext("Product attribute value", "No")

    @property
    def value_as_html(self):
        """
        Returns a HTML representation of the attribute's value. To customise
        e.g. image attribute values, declare a ``_image_as_html`` property and
        return e.g. an ``<img>`` tag.  Defaults to the ``_as_text``
        representation.
        """
        property_name = "_%s_as_html" % self.type
        return getattr(self, property_name, self.value_as_text)

    @property
    def _richtext_as_html(self):
        return mark_safe(self.value)



# это ок/   prod_id -- variant_id
class AbstractProductVariantGroup(models.Model):
    """
    Joining model between products and variants. Exists to allow customising.
    """

    product = models.ForeignKey(
        "catalogue.Product", on_delete=models.CASCADE, verbose_name=_("Product")
    )

    variant = models.ForeignKey(
        "catalogue.ProductVariant", on_delete=models.CASCADE, verbose_name=_("Product Variant")
    )

    class Meta:
        abstract = True
        app_label = "catalogue"
        ordering = ["product", "variant"]
        unique_together = ("product", "variant")
        verbose_name = _("Product variant")
        verbose_name_plural = _("Product variants")

    def __str__(self):
        return "<productcategory for product '%s'>" % self.product














































class AbstractProduct(models.Model):
    """
    The base product object

    There's three kinds of products; they're distinguished by the structure
    field.

    - A stand alone product. Regular product that lives by itself.
    - A child product. All child products have a parent product. They're a
      specific version of the parent.
    - A parent product. It essentially represents a set of products.

    An example could be a yoga course, which is a parent product. The different
    times/locations of the courses would be associated with the child products.
    """

    STANDALONE, PARENT, CHILD = "standalone", "parent", "child"
    STRUCTURE_CHOICES = (
        (STANDALONE, _("Stand-alone product")),
        (PARENT, _("Parent product")),
        (CHILD, _("Child product")),
    )

    structure = models.CharField(
        _("Product structure"),
        max_length=10,
        choices=STRUCTURE_CHOICES,
        default=STANDALONE,
    )

    is_public = models.BooleanField(
        _("Is public"),
        default=True,
        db_index=True,
        help_text=_("Show this product in search results and catalogue listings."),
    )




    upc = NullCharField(
        _("UPC"),
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        help_text=_(
            "Universal Product Code (UPC) is an identifier for "
            "a product which is not specific to a particular "
            " supplier. Eg an ISBN for a book."
        ),
    )

    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="children",
        verbose_name=_("Parent product"),
        help_text=_(
            "Only choose a parent product if you're creating a child "
            "product.  For example if this is a size "
            "4 of a particular t-shirt.  Leave blank if this is a "
            "stand-alone product (i.e. there is only one version of"
            " this product)."
        ),
    )

    # Title is mandatory for canonical products but optional for child products
    title = models.CharField(
        pgettext_lazy("Product title", "Title"), max_length=255, blank=True
    )
    slug = SlugField(_("Slug"), max_length=255, unique=False)
    description = models.TextField(_("Description"), blank=True)
    meta_title = models.CharField(
        _("Meta title"), max_length=255, blank=True, null=True
    )
    meta_description = models.TextField(_("Meta description"), blank=True, null=True)

    #: "Kind" of product, e.g. T-Shirt, Book, etc.
    #: None for child products, they inherit their parent's product class
    product_class = models.ForeignKey(
        "catalogue.ProductClass",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_("Product type"),
        related_name="products",
        help_text=_("Choose what type of product this is"),
    )
    attributes = models.ManyToManyField(
        "catalogue.ProductAttribute",
        through="ProductAttributeValue",
        verbose_name=_("Attributes"),
        help_text=_(
            "A product attribute is something that this product may "
            "have, such as a size, as specified by its class"
        ),
    )
    #: It's possible to have options product class-wide, and per product.
    product_options = models.ManyToManyField(
        "catalogue.Option",
        blank=True,
        verbose_name=_("Product options"),
        help_text=_(
            "Options are values that can be associated with a item "
            "when it is added to a customer's basket.  This could be "
            "something like a personalised message to be printed on "
            "a T-shirt."
        ),
    )

    recommended_products = models.ManyToManyField(
        "catalogue.Product",
        through="ProductRecommendation",
        blank=True,
        verbose_name=_("Recommended products"),
        help_text=_(
            "These are products that are recommended to accompany the main product."
        ),
    )

    # Denormalised product rating - used by reviews app.
    # Product has no ratings if rating is None
    rating = models.FloatField(_("Rating"), null=True, editable=False)

    date_created = models.DateTimeField(
        _("Date created"), auto_now_add=True, db_index=True
    )

    # This field is used by Haystack to reindex search
    date_updated = models.DateTimeField(_("Date updated"), auto_now=True, db_index=True)

    categories = models.ManyToManyField(
        "catalogue.Category", through="ProductCategory", verbose_name=_("Categories")
    )

    #: Determines if a product may be used in an offer. It is illegal to
    #: discount some types of product (e.g. ebooks) and this field helps
    #: merchants from avoiding discounting such products
    #: Note that this flag is ignored for child products; they inherit from
    #: the parent product.
    is_discountable = models.BooleanField(
        _("Is discountable?"),
        default=True,
        help_text=_(
            "This flag indicates if this product can be used in an offer or not"
        ),
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        abstract = True
        app_label = "catalogue"
        ordering = ["-date_created"]
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attr = ProductAttributesContainer(product=self)

    def __str__(self):
        if self.title:
            return self.title
        if self.attribute_summary:
            return "%s (%s)" % (self.get_title(), self.attribute_summary)
        else:
            return self.get_title()

    def get_absolute_url(self):
        """
        Return a product's absolute URL
        """
        return reverse(
            "catalogue:detail", kwargs={"product_slug": self.slug, "pk": self.id}
        )

    def clean(self):
        """
        Validate a product. Those are the rules:

        +---------------+-------------+--------------+--------------+
        |               | stand alone | parent       | child        |
        +---------------+-------------+--------------+--------------+
        | title         | required    | required     | optional     |
        +---------------+-------------+--------------+--------------+
        | product class | required    | required     | must be None |
        +---------------+-------------+--------------+--------------+
        | parent        | forbidden   | forbidden    | required     |
        +---------------+-------------+--------------+--------------+
        | stockrecords  | 0 or more   | forbidden    | 0 or more    |
        +---------------+-------------+--------------+--------------+
        | categories    | 1 or more   | 1 or more    | forbidden    |
        +---------------+-------------+--------------+--------------+
        | attributes    | optional    | optional     | optional     |
        +---------------+-------------+--------------+--------------+
        | rec. products | optional    | optional     | unsupported  |
        +---------------+-------------+--------------+--------------+
        | options       | optional    | optional     | forbidden    |
        +---------------+-------------+--------------+--------------+

        Because the validation logic is quite complex, validation is delegated
        to the sub method appropriate for the product's structure.
        """
        getattr(self, "_clean_%s" % self.structure)()
        if not self.is_parent:
            self.attr.validate_attributes()

    def _clean_standalone(self):
        """
        Validates a stand-alone product
        """
        if not self.title:
            raise ValidationError(_("Your product must have a title."))
        if not self.product_class:
            raise ValidationError(_("Your product must have a product class."))
        if self.parent_id:
            raise ValidationError(_("Only child products can have a parent."))

    def _clean_child(self):
        """
        Validates a child product
        """
        has_parent = self.parent or self.parent_id

        if not has_parent:
            raise ValidationError(_("A child product needs a parent."))
        if has_parent and not self.parent.is_parent:
            raise ValidationError(
                _("You can only assign child products to parent products.")
            )
        if self.product_class:
            raise ValidationError(_("A child product can't have a product class."))
        if self.pk and self.categories.exists():
            raise ValidationError(_("A child product can't have a category assigned."))
        # Note that we only forbid options on product level
        if self.pk and self.product_options.exists():
            raise ValidationError(_("A child product can't have options."))

    def _clean_parent(self):
        """
        Validates a parent product.
        """
        self._clean_standalone()
        if self.has_stockrecords:
            raise ValidationError(_("A parent product can't have stockrecords."))

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.get_title())
        super().save(*args, **kwargs)
        self.attr.save()

    def refresh_from_db(self, using=None, fields=None):
        super().refresh_from_db(using, fields)
        self.attr.invalidate()

    # Properties

    @property
    def is_standalone(self):
        return self.structure == self.STANDALONE

    @property
    def is_parent(self):
        return self.structure == self.PARENT

    @property
    def is_child(self):
        return self.structure == self.CHILD

    def can_be_parent(self, give_reason=False):
        """
        Helps decide if a the product can be turned into a parent product.
        """
        reason = None
        if self.is_child:
            reason = _("The specified parent product is a child product.")
        if self.has_stockrecords:
            reason = _("One can't add a child product to a product with stock records.")
        is_valid = reason is None
        if give_reason:
            return is_valid, reason
        else:
            return is_valid

    @property
    def options(self):
        """
        Returns a set of all valid options for this product.
        It's possible to have options product class-wide, and per product.
        """
        pclass_options = self.get_product_class().options.all()
        return pclass_options | self.product_options.all()

    @cached_property
    def has_options(self):
        # Extracting annotated value with number of product class options
        # from product list queryset.
        has_product_class_options = getattr(self, "has_product_class_options", None)
        has_product_options = getattr(self, "has_product_options", None)
        if has_product_class_options is not None and has_product_options is not None:
            return has_product_class_options or has_product_options
        return self.options.exists()

    @property
    def is_shipping_required(self):
        return self.get_product_class().requires_shipping

    @property
    def has_stockrecords(self):
        """
        Test if this product has any stockrecords
        """
        if self.id:
            return self.stockrecords.exists()
        return False

    @property
    def num_stockrecords(self):
        return self.stockrecords.count()

    @property
    def attribute_summary(self):
        """
        Return a string of all of a product's attributes
        """
        attributes = self.get_attribute_values()
        pairs = [attribute.summary() for attribute in attributes]
        return ", ".join(pairs)

    def get_title(self):
        """
        Return a product's title or it's parent's title if it has no title
        """
        title = self.title
        if not title and self.parent_id:
            title = self.parent.title
        return title

    get_title.short_description = pgettext_lazy("Product title", "Title")

    def get_meta_title(self):
        title = self.meta_title
        if not title and self.is_child:
            title = self.parent.meta_title
        return title or self.get_title()

    get_meta_title.short_description = pgettext_lazy("Product meta title", "Meta title")

    def get_meta_description(self):
        meta_description = self.meta_description
        if not meta_description and self.is_child:
            meta_description = self.parent.meta_description
        return meta_description or striptags(self.description)

    get_meta_description.short_description = pgettext_lazy(
        "Product meta description", "Meta description"
    )

    def get_product_class(self):
        """
        Return a product's item class. Child products inherit their parent's.
        """
        if self.is_child:
            return self.parent.product_class
        else:
            return self.product_class

    get_product_class.short_description = _("Product class")

    @deprecated
    def get_is_discountable(self):
        """
        It used to be that, :py:attr:`.is_discountable` couldn't be set individually for child
        products; so they had to inherit it from their parent. This is nolonger the case because
        ranges can include child products as well. That make this method useless.
        """
        return self.is_discountable

    # pylint: disable=no-member
    def get_categories(self):
        """
        Return a product's public categories or parent's if there is a parent product.
        """
        if self.is_child:
            return self.parent.categories.browsable()
        else:
            return self.categories.browsable()

    get_categories.short_description = _("Categories")

    def get_attribute_values(self):
        if not self.pk:
            return self.attribute_values.model.objects.none()

        attribute_values = self.attribute_values.all()
        if self.is_child:
            parent_attribute_values = self.parent.attribute_values.exclude(
                attribute__code__in=attribute_values.values("attribute__code")
            )
            return attribute_values | parent_attribute_values

        return attribute_values

    # Images

    def get_missing_image(self):
        """
        Returns a missing image object.
        """
        # This class should have a 'name' property so it mimics the Django file
        # field.
        return MissingProductImage()

    # pylint: disable=no-member
    def get_all_images(self):
        if self.is_child and not self.images.exists() and self.parent_id is not None:
            return self.parent.images.all()
        return self.images.all()

    def primary_image(self):
        """
        Returns the primary image for a product. Usually used when one can
        only display one product image, e.g. in a list of products.
        """
        images = self.get_all_images()
        ordering = self.images.model.Meta.ordering
        if not ordering or ordering[0] != "display_order":
            # Only apply order_by() if a custom model doesn't use default
            # ordering. Applying order_by() busts the prefetch cache of
            # the ProductManager
            images = images.order_by("display_order")
        try:
            return images[0]
        except IndexError:
            # We return a dict with fields that mirror the key properties of
            # the ProductImage class so this missing image can be used
            # interchangeably in templates.  Strategy pattern ftw!
            missing_image = self.get_missing_image()
            return {"original": missing_image.name, "caption": "", "is_missing": True}

    # Updating methods

    def update_rating(self):
        """
        Recalculate rating field
        """
        self.rating = self.calculate_rating()
        self.save()

    update_rating.alters_data = True

    # pylint: disable=no-member
    def calculate_rating(self):
        """
        Calculate rating value
        """
        result = self.reviews.filter(status=self.reviews.model.APPROVED).aggregate(
            sum=Sum("score"), count=Count("id")
        )
        reviews_sum = result["sum"] or 0
        reviews_count = result["count"] or 0
        rating = None
        if reviews_count > 0:
            rating = float(reviews_sum) / reviews_count
        return rating

    def has_review_by(self, user):
        if user.is_anonymous:
            return False
        return self.reviews.filter(user=user).exists()

    def is_review_permitted(self, user):
        """
        Determines whether a user may add a review on this product.

        Default implementation respects OSCAR_ALLOW_ANON_REVIEWS and only
        allows leaving one review per user and product.

        Override this if you want to alter the default behaviour; e.g. enforce
        that a user purchased the product to be allowed to leave a review.
        """
        if user.is_authenticated or settings.OSCAR_ALLOW_ANON_REVIEWS:
            return not self.has_review_by(user)
        else:
            return False

    @cached_property
    def num_approved_reviews(self):
        return self.reviews.approved().count()

    @property
    def sorted_recommended_products(self):
        """Keeping order by recommendation ranking."""
        return [
            r.recommendation
            for r in self.primary_recommendations.select_related("recommendation").all()
        ]






























































class AbstractProduct(models.Model):
    """
    The base product object

    There's three kinds of products; they're distinguished by the structure
    field.

    - A stand alone product. Regular product that lives by itself.
    - A child product. All child products have a parent product. They're a
      specific version of the parent.
    - A parent product. It essentially represents a set of products.

    An example could be a yoga course, which is a parent product. The different
    times/locations of the courses would be associated with the child products.
    """

    SIMPLE, VARIABLE = "simple", "variable"
    STRUCTURE_CHOICES = (
        (SIMPLE, _("Simple product")),
        (VARIABLE, _("Variable product"))
    )

    structure = models.CharField(
        _("Product structure"),
        max_length=10,
        choices=STRUCTURE_CHOICES,
        default=SIMPLE,
    )

    variants = models.ForeignKey(
        "catalogue.Vatiant",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="product_variants",
        verbose_name=_("Variants"),
        help_text=_('Select an variants group if using type "variable"'),
    )


    is_public = models.BooleanField(
        _("Is public"),
        default=True,
        db_index=True,
        help_text=_("Show this product in search results and catalogue listings."),
    )

    upc = NullCharField(
        _("UPC"),
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        help_text=_(
            "Universal Product Code (UPC) is an identifier for "
            "a product which is not specific to a particular "
            " supplier. Eg an ISBN for a book."
        ),
    )

    # Title is mandatory for canonical products but optional for child products
    title = models.CharField(
        pgettext_lazy("Product title", "Title"), max_length=255, blank=True
    )
    slug = SlugField(_("Slug"), max_length=255, unique=False)
    description = models.TextField(_("Description"), blank=True)
    meta_title = models.CharField(
        _("Meta title"), max_length=255, blank=True, null=True
    )
    meta_description = models.TextField(_("Meta description"), blank=True, null=True)

    #: "Kind" of product, e.g. T-Shirt, Book, etc.
    #: None for child products, they inherit their parent's product class
    product_class = models.ForeignKey(
        "catalogue.ProductClass",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_("Product type"),
        related_name="products",
        help_text=_("Choose what type of product this is"),
    )

    attributes = models.ManyToManyField(
        "catalogue.ProductAttribute",
        through="ProductAttributeValue",
        verbose_name=_("Attributes"),
        help_text=_(
            "A product attribute is something that this product may "
            "have, such as a size, as specified by its class"
        ),
    )

    #: It's possible to have options product class-wide, and per product.
    product_options = models.ManyToManyField(
        "catalogue.Option",
        blank=True,
        verbose_name=_("Product options"),
        help_text=_(
            "Options are values that can be associated with a item "
            "when it is added to a customer's basket.  This could be "
            "something like a personalised message to be printed on "
            "a T-shirt."
        ),
    )

    recommended_products = models.ManyToManyField(
        "catalogue.Product",
        through="ProductRecommendation",
        blank=True,
        verbose_name=_("Recommended products"),
        help_text=_(
            "These are products that are recommended to accompany the main product."
        ),
    )

    # Denormalised product rating - used by reviews app.
    # Product has no ratings if rating is None
    rating = models.FloatField(_("Rating"), null=True, editable=False)

    date_created = models.DateTimeField(
        _("Date created"), auto_now_add=True, db_index=True
    )

    # This field is used by Haystack to reindex search
    date_updated = models.DateTimeField(_("Date updated"), auto_now=True, db_index=True)

    categories = models.ManyToManyField(
        "catalogue.Category", through="ProductCategory", verbose_name=_("Categories")
    )

    #: Determines if a product may be used in an offer. It is illegal to
    #: discount some types of product (e.g. ebooks) and this field helps
    #: merchants from avoiding discounting such products
    #: Note that this flag is ignored for child products; they inherit from
    #: the parent product.
    is_discountable = models.BooleanField(
        _("Is discountable?"),
        default=True,
        help_text=_(
            "This flag indicates if this product can be used in an offer or not"
        ),
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        abstract = True
        app_label = "catalogue"
        ordering = ["-date_created"]
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attr = ProductAttributesContainer(product=self)

    def __str__(self):
        if self.title:
            return self.title
        if self.attribute_summary:
            return "%s (%s)" % (self.get_title(), self.attribute_summary)
        else:
            return self.get_title()

    def get_absolute_url(self):
        """
        Return a product's absolute URL
        """
        return reverse(
            "catalogue:detail", kwargs={"product_slug": self.slug, "pk": self.id}
        )

    def clean(self):
        """
        Validate a product. Those are the rules:

        +---------------+-------------+--------------+--------------+
        |               | stand alone | parent       | child        |
        +---------------+-------------+--------------+--------------+
        | title         | required    | required     | optional     |
        +---------------+-------------+--------------+--------------+
        | product class | required    | required     | must be None |
        +---------------+-------------+--------------+--------------+
        | parent        | forbidden   | forbidden    | required     |
        +---------------+-------------+--------------+--------------+
        | stockrecords  | 0 or more   | forbidden    | 0 or more    |
        +---------------+-------------+--------------+--------------+
        | categories    | 1 or more   | 1 or more    | forbidden    |
        +---------------+-------------+--------------+--------------+
        | attributes    | optional    | optional     | optional     |
        +---------------+-------------+--------------+--------------+
        | rec. products | optional    | optional     | unsupported  |
        +---------------+-------------+--------------+--------------+
        | options       | optional    | optional     | forbidden    |
        +---------------+-------------+--------------+--------------+

        Because the validation logic is quite complex, validation is delegated
        to the sub method appropriate for the product's structure.
        """
        getattr(self, "_clean_%s" % self.structure)()
        # if not self.is_parent:
        #     self.attr.validate_attributes()

    def _clean_standalone(self):
        """
        Validates a stand-alone product
        """
        if not self.title:
            raise ValidationError(_("Your product must have a title."))
        if not self.product_class:
            raise ValidationError(_("Your product must have a product class."))
        if self.parent_id:
            raise ValidationError(_("Only child products can have a parent."))

    # def _clean_child(self):
    #     """
    #     Validates a child product
    #     """
    #     has_parent = self.parent or self.parent_id

    #     if not has_parent:
    #         raise ValidationError(_("A child product needs a parent."))
    #     if has_parent and not self.parent.is_parent:
    #         raise ValidationError(
    #             _("You can only assign child products to parent products.")
    #         )
    #     if self.product_class:
    #         raise ValidationError(_("A child product can't have a product class."))
    #     if self.pk and self.categories.exists():
    #         raise ValidationError(_("A child product can't have a category assigned."))
    #     # Note that we only forbid options on product level
    #     if self.pk and self.product_options.exists():
    #         raise ValidationError(_("A child product can't have options."))

    # def _clean_parent(self):
        """
        Validates a parent product.
        """
        self._clean_standalone()
        if self.has_stockrecords:
            raise ValidationError(_("A parent product can't have stockrecords."))

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.get_title())
        super().save(*args, **kwargs)
        self.attr.save()

    def refresh_from_db(self, using=None, fields=None):
        super().refresh_from_db(using, fields)
        self.attr.invalidate()

    # Properties

    # @property
    # def is_standalone(self):
    #     return self.structure == self.STANDALONE

    # @property
    # def is_parent(self):
    #     return self.structure == self.PARENT

    # @property
    # def is_child(self):
    #     return self.structure == self.CHILD

    # def can_be_parent(self, give_reason=False):
    #     """
    #     Helps decide if a the product can be turned into a parent product.
    #     """
    #     reason = None
    #     if self.is_child:
    #         reason = _("The specified parent product is a child product.")
    #     if self.has_stockrecords:
    #         reason = _("One can't add a child product to a product with stock records.")
    #     is_valid = reason is None
    #     if give_reason:
    #         return is_valid, reason
    #     else:
    #         return is_valid

    @property
    def is_simple(self):
        return self.structure == self.SIMPLE

    @property
    def is_variable(self):
        return self.structure == self.VARIABLE


    @property
    def options(self):
        """
        Returns a set of all valid options for this product.
        It's possible to have options product class-wide, and per product.
        """
        pclass_options = self.get_product_class().options.all()
        return pclass_options | self.product_options.all()

    @cached_property
    def has_options(self):
        # Extracting annotated value with number of product class options
        # from product list queryset.
        has_product_class_options = getattr(self, "has_product_class_options", None)
        has_product_options = getattr(self, "has_product_options", None)
        if has_product_class_options is not None and has_product_options is not None:
            return has_product_class_options or has_product_options
        return self.options.exists()

    @property
    def is_shipping_required(self):
        return self.get_product_class().requires_shipping

    @property
    def has_stockrecords(self):
        """
        Test if this product has any stockrecords
        """
        if self.id:
            return self.stockrecords.exists()
        return False

    @property
    def num_stockrecords(self):
        return self.stockrecords.count()

    @property
    def attribute_summary(self):
        """
        Return a string of all of a product's attributes
        """
        attributes = self.get_attribute_values()
        pairs = [attribute.summary() for attribute in attributes]
        return ", ".join(pairs)

    def get_title(self):
        """
        Return a product's title or it's parent's title if it has no title
        """
        title = self.title
        # if not title and self.parent_id:
        #     title = self.parent.title
        return title

    get_title.short_description = pgettext_lazy("Product title", "Title")

    def get_meta_title(self):
        title = self.meta_title
        if not title and self.is_child:
            title = self.parent.meta_title
        return title or self.get_title()

    get_meta_title.short_description = pgettext_lazy("Product meta title", "Meta title")

    def get_meta_description(self):
        meta_description = self.meta_description
        if not meta_description and self.is_child:
            meta_description = self.parent.meta_description
        return meta_description or striptags(self.description)

    get_meta_description.short_description = pgettext_lazy(
        "Product meta description", "Meta description"
    )

    def get_product_class(self):
        """
        Return a product's item class. Child products inherit their parent's.
        """
        if self.is_child:
            return self.parent.product_class
        else:
            return self.product_class

    get_product_class.short_description = _("Product class")

    @deprecated
    def get_is_discountable(self):
        """
        It used to be that, :py:attr:`.is_discountable` couldn't be set individually for child
        products; so they had to inherit it from their parent. This is nolonger the case because
        ranges can include child products as well. That make this method useless.
        """
        return self.is_discountable

    # pylint: disable=no-member
    def get_categories(self):
        """
        Return a product's public categories or parent's if there is a parent product.
        """
        if self.is_child:
            return self.parent.categories.browsable()
        else:
            return self.categories.browsable()

    get_categories.short_description = _("Categories")

    def get_attribute_values(self):
        if not self.pk:
            return self.attribute_values.model.objects.none()

        attribute_values = self.attribute_values.all()
        if self.is_child:
            parent_attribute_values = self.parent.attribute_values.exclude(
                attribute__code__in=attribute_values.values("attribute__code")
            )
            return attribute_values | parent_attribute_values

        return attribute_values

    # Images

    def get_missing_image(self):
        """
        Returns a missing image object.
        """
        # This class should have a 'name' property so it mimics the Django file
        # field.
        return MissingProductImage()

    # pylint: disable=no-member
    def get_all_images(self):
        if self.is_child and not self.images.exists() and self.parent_id is not None:
            return self.parent.images.all()
        return self.images.all()

    def primary_image(self):
        """
        Returns the primary image for a product. Usually used when one can
        only display one product image, e.g. in a list of products.
        """
        images = self.get_all_images()
        ordering = self.images.model.Meta.ordering
        if not ordering or ordering[0] != "display_order":
            # Only apply order_by() if a custom model doesn't use default
            # ordering. Applying order_by() busts the prefetch cache of
            # the ProductManager
            images = images.order_by("display_order")
        try:
            return images[0]
        except IndexError:
            # We return a dict with fields that mirror the key properties of
            # the ProductImage class so this missing image can be used
            # interchangeably in templates.  Strategy pattern ftw!
            missing_image = self.get_missing_image()
            return {"original": missing_image.name, "caption": "", "is_missing": True}

    # Updating methods

    def update_rating(self):
        """
        Recalculate rating field
        """
        self.rating = self.calculate_rating()
        self.save()

    update_rating.alters_data = True

    # pylint: disable=no-member
    def calculate_rating(self):
        """
        Calculate rating value
        """
        result = self.reviews.filter(status=self.reviews.model.APPROVED).aggregate(
            sum=Sum("score"), count=Count("id")
        )
        reviews_sum = result["sum"] or 0
        reviews_count = result["count"] or 0
        rating = None
        if reviews_count > 0:
            rating = float(reviews_sum) / reviews_count
        return rating

    def has_review_by(self, user):
        if user.is_anonymous:
            return False
        return self.reviews.filter(user=user).exists()

    def is_review_permitted(self, user):
        """
        Determines whether a user may add a review on this product.

        Default implementation respects OSCAR_ALLOW_ANON_REVIEWS and only
        allows leaving one review per user and product.

        Override this if you want to alter the default behaviour; e.g. enforce
        that a user purchased the product to be allowed to leave a review.
        """
        if user.is_authenticated or settings.OSCAR_ALLOW_ANON_REVIEWS:
            return not self.has_review_by(user)
        else:
            return False

    @cached_property
    def num_approved_reviews(self):
        return self.reviews.approved().count()

    @property
    def sorted_recommended_products(self):
        """Keeping order by recommendation ranking."""
        return [
            r.recommendation
            for r in self.primary_recommendations.select_related("recommendation").all()
        ]





# class AbstractProductType(models.Model):

#     SIMPLE, VARIANT = "simple", "variant"
#     TYPE_CHOICES = (
#         (SIMPLE, _("Simple product")),
#         (VARIANT, _("Variant product"))
#     )

#     # variety = models.ManyToManyField(Variety, related_name='children', verbose_name='Родитель')


#     # type = models.CharField(
#     #     _("Product structure"),
#     #     max_length=10,
#     #     choices=TYPE_CHOICES,
#     #     default=SIMPLE,
#     # )

#     name = models.CharField(max_length=250,)
#     slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)

#     class Meta:
#         ordering = ("slug",)
#         app_label = "catalogue"

#     def __str__(self) -> str:
#         return self.name

#     def __repr__(self) -> str:
#         class_ = type(self)
#         return f"<{class_.__module__}.{class_.__name__}(pk={self.pk!r}, name={self.name!r})>"

# class AbstractVariantProduct(models.Model):

#     name = models.CharField(max_length=250,)
#     slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)

#     variants_options = models.ManyToManyField(
#         "catalogue.Option", blank=True, verbose_name=_("Options")
#     )

#     class Meta:
#         ordering = ("slug",)
#         app_label = "catalogue"

#     def __str__(self) -> str:
#         return self.name

#     def __repr__(self) -> str:
#         class_ = type(self)
#         return f"<{class_.__module__}.{class_.__name__}(pk={self.pk!r}, name={self.name!r})>"

# class AbstractSimpleProduct(models.Model):
    
#     name = models.CharField(max_length=250,)
#     slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)

#     class Meta:
#         ordering = ("slug",)
#         app_label = "catalogue"

#     def __str__(self) -> str:
#         return self.name

# class AbstractAdditionalProduct(models.Model):
#     name = models.CharField(max_length=250,)
#     slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
#     img = models.ImageField()
#     weight = models.IntegerField()
#     price = models.DecimalField(default=1)
#     max_count = models.IntegerField(default=2)

#     class Meta:
#         ordering = ("slug",)
#         app_label = "catalogue"

#     def __str__(self) -> str:
#         return self.name









# class Variety(models.Model):

#     varietyName = models.CharField(max_length=30)
#     varietyPrice = models.DecimalField()

#     def __str__(self):
#         return self.varietyName

#     class Meta:
#         verbose_name = "Список вариации"
#         verbose_name_plural = "Список вариаций"










# # это ок/   заголовок вариации
# class AbstractVariant(models.Model):
#     """
#     Defines a Variants that collectively may be used as an
#     attribute type

#     For example, Language
#     """

#     name = models.CharField(_("Name"), max_length=128)

#     code = NullCharField(
#         _("Unique identifier"),
#         max_length=255,
#         blank=True,
#         null=True,
#         unique=True,
#     )

#     def __str__(self):
#         return self.name

#     class Meta:
#         abstract = True
#         app_label = "catalogue"
#         verbose_name = _("Variant group")
#         verbose_name_plural = _("Variants group")

#     # @property
#     # def option_summary(self):
#     #     options = [o.option for o in self.options.all()]
#     #     return ", ".join(options)



# # это ок/   значения вариации
# class AbstractVariantValue(models.Model):
#     """
#     Provides an option within an variants group for an attribute type
#     Examples: In a Language group, English, Greek, French
#     """

#     variant = models.ForeignKey(
#         "catalogue.Variant",
#         on_delete=models.CASCADE,
#         related_name="variant",
#         verbose_name=_("Group"),
#     )

#     option = models.CharField(_("Option"), max_length=255)
    
#     code = NullCharField(
#         _("Unique identifier"),
#         max_length=255,
#         blank=True,
#         null=True,
#         unique=True,
#     )

#     def __str__(self):
#         return self.option

#     class Meta:
#         abstract = True
#         app_label = "catalogue"
#         unique_together = ("variant", "option")
#         verbose_name = _("Attribute option")
#         verbose_name_plural = _("Attribute options")



# # не сделал /   вариант продукты на основе вариаций выше
# class AbstractProductVariant(models.Model):

#     variant = models.ForeignKey(
#         "catalogue.VariantValue",
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name="ProductVariant",
#         verbose_name=_("Product"),
#         help_text=_('Select an variants group if using type "variable"'),
#     )

#     price_currency = models.CharField(
#         _("Currency"), max_length=12, default=get_default_currency
#     )

#     old_price = models.DecimalField(
#         _("Old price"), 
#         decimal_places=2,
#         max_digits=12, 
#         blank=True, 
#         null=True,
#         help_text=_('Show old price'),
#     )

#     price = models.DecimalField(
#         _("Price"), 
#         decimal_places=2,
#         max_digits=12, 
#         blank=True, 
#         null=True,
#         help_text=_('Show price'),
#     )

#     is_public = models.BooleanField(
#         _("Is public"),
#         default=True,
#         db_index=True,
#         help_text=_("Show this product in search results and catalogue listings."),
#     )

#     time_to_make = models.IntegerField(
#         _("Time"),
#         default=60,
#         db_index=True,
#         help_text=_("Time to make the dich in minetes."),
#     )
    
#     date_updated = models.DateTimeField(_("Date updated"), auto_now=True, db_index=True)


# class AbstractProduct(models.Model):
#     """
#     The base product object

#     There's three kinds of products; they're distinguished by the structure
#     field.

#     - A stand alone product. Regular product that lives by itself.
#     - A child product. All child products have a parent product. They're a
#       specific version of the parent.
#     - A parent product. It essentially represents a set of products.

#     An example could be a yoga course, which is a parent product. The different
#     times/locations of the courses would be associated with the child products.
#     """


#     # to delite potom
#     STANDALONE, PARENT, CHILD = "standalone", "parent", "child"
#     STRUCTURE_CHOICES = (
#         (STANDALONE, _("Stand-alone product")),
#         (PARENT, _("Parent product")),
#         (CHILD, _("Child product")),
#     )
#     structure = models.CharField(
#         _("Product structure"),
#         max_length=10,
#         choices=STRUCTURE_CHOICES,
#         default=STANDALONE,
#     )    
#     parent = models.ForeignKey(
#         "self",
#         blank=True,
#         null=True,
#         on_delete=models.CASCADE,
#         related_name="children",
#         verbose_name=_("Parent product"),
#         help_text=_(
#             "Only choose a parent product if you're creating a child "
#             "product.  For example if this is a size "
#             "4 of a particular t-shirt.  Leave blank if this is a "
#             "stand-alone product (i.e. there is only one version of"
#             " this product)."
#         ),
#     )
#     def clean(self):
#         """
#         Validate a product. Those are the rules:

#         +---------------+-------------+--------------+--------------+
#         |               | stand alone | parent       | child        |
#         +---------------+-------------+--------------+--------------+
#         | title         | required    | required     | optional     |
#         +---------------+-------------+--------------+--------------+
#         | product class | required    | required     | must be None |
#         +---------------+-------------+--------------+--------------+
#         | parent        | forbidden   | forbidden    | required     |
#         +---------------+-------------+--------------+--------------+
#         | stockrecords  | 0 or more   | forbidden    | 0 or more    |
#         +---------------+-------------+--------------+--------------+
#         | categories    | 1 or more   | 1 or more    | forbidden    |
#         +---------------+-------------+--------------+--------------+
#         | attributes    | optional    | optional     | optional     |
#         +---------------+-------------+--------------+--------------+
#         | rec. products | optional    | optional     | unsupported  |
#         +---------------+-------------+--------------+--------------+
#         | options       | optional    | optional     | forbidden    |
#         +---------------+-------------+--------------+--------------+

#         Because the validation logic is quite complex, validation is delegated
#         to the sub method appropriate for the product's structure.
#         """
#         getattr(self, "_clean_%s" % self.structure)()
#         if not self.is_parent:
#             self.attr.validate_attributes()
#     def _clean_standalone(self):
#         """
#         Validates a stand-alone product
#         """
#         if not self.title:
#             raise ValidationError(_("Your product must have a title."))
#         if not self.product_class:
#             raise ValidationError(_("Your product must have a product class."))
#         if self.parent_id:
#             raise ValidationError(_("Only child products can have a parent."))
#     def _clean_child(self):
#         """
#         Validates a child product
#         """
#         has_parent = self.parent or self.parent_id

#         if not has_parent:
#             raise ValidationError(_("A child product needs a parent."))
#         if has_parent and not self.parent.is_parent:
#             raise ValidationError(
#                 _("You can only assign child products to parent products.")
#             )
#         if self.product_class:
#             raise ValidationError(_("A child product can't have a product class."))
#         if self.pk and self.categories.exists():
#             raise ValidationError(_("A child product can't have a category assigned."))
#         # Note that we only forbid options on product level
#         if self.pk and self.product_options.exists():
#             raise ValidationError(_("A child product can't have options."))
#     def _clean_parent(self):
#         """
#         Validates a parent product.
#         """
#         self._clean_standalone()
#         if self.has_stockrecords:
#             raise ValidationError(_("A parent product can't have stockrecords."))
#     @property
#     def is_standalone(self):
#         return self.structure == self.STANDALONE
#     @property
#     def is_parent(self):
#         return self.structure == self.PARENT
#     @property
#     def is_child(self):
#         return self.structure == self.CHILD
#     def can_be_parent(self, give_reason=False):
#         """
#         Helps decide if a the product can be turned into a parent product.
#         """
#         reason = None
#         if self.is_child:
#             reason = _("The specified parent product is a child product.")
#         if self.has_stockrecords:
#             reason = _("One can't add a child product to a product with stock records.")
#         is_valid = reason is None
#         if give_reason:
#             return is_valid, reason
#         else:
#             return is_valid















#     # i did
#     SIMPLE, VARIANT = "simple", "variant"
#     TYPE_CHOICES = (
#         (SIMPLE, _("Simple product")),
#         (VARIANT, _("Variable product"))
#     )

#     type = models.CharField(
#         _("Product structure"),
#         max_length=10,
#         choices=TYPE_CHOICES,
#         default=SIMPLE,
#     )

#     # я хз надо ли это поле    
#     # product_variations = models.ManyToManyField(
#     #     "catalogue.ProductVariant",
#     #     blank=True,
#     #     through="VariantValue",
#     #     verbose_name=_("Product variants"),
#     #     help_text=_(
#     #         "Options are values that can be associated with a item "
#     #         "when it is added to a customer's basket.  This could be "
#     #         "something like a personalised message to be printed on "
#     #         "a T-shirt."
#     #     ),
#     # )

#     # @property
#     # def has_variants(self):
#     #     """
#     #     Test if this product has more than 1 variants
#     #     """
#     #     if self.id:
#     #         return self.variants.count() > 1 and self.VARIANT
#     #     return False















#     is_public = models.BooleanField(
#         _("Is public"),
#         default=True,
#         db_index=True,
#         help_text=_("Show this product in search results and catalogue listings."),
#     )

#     upc = NullCharField(
#         _("UPC"),
#         max_length=64,
#         blank=True,
#         null=True,
#         unique=True,
#         help_text=_(
#             "Universal Product Code (UPC) is an identifier for "
#             "a product which is not specific to a particular "
#             " supplier. Eg an ISBN for a book."
#         ),
#     )



#     # Title is mandatory for canonical products but optional for child products
#     title = models.CharField(
#         pgettext_lazy("Product title", "Title"), max_length=255, blank=True
#     )
#     slug = SlugField(_("Slug"), max_length=255, unique=False)
#     description = models.TextField(_("Description"), blank=True)
#     meta_title = models.CharField(
#         _("Meta title"), max_length=255, blank=True, null=True
#     )
#     meta_description = models.TextField(_("Meta description"), blank=True, null=True)

#     #: "Kind" of product, e.g. T-Shirt, Book, etc.
#     #: None for child products, they inherit their parent's product class
#     product_class = models.ForeignKey(
#         "catalogue.ProductClass",
#         null=True,
#         blank=True,
#         on_delete=models.PROTECT,
#         verbose_name=_("Product type"),
#         related_name="products",
#         help_text=_("Choose what type of product this is"),
#     )
#     attributes = models.ManyToManyField(
#         "catalogue.ProductAttribute",
#         through="ProductAttributeValue",
#         verbose_name=_("Attributes"),
#         help_text=_(
#             "A product attribute is something that this product may "
#             "have, such as a size, as specified by its class"
#         ),
#     )
#     #: It's possible to have options product class-wide, and per product.
#     product_options = models.ManyToManyField(
#         "catalogue.Option",
#         blank=True,
#         verbose_name=_("Product options"),
#         help_text=_(
#             "Options are values that can be associated with a item "
#             "when it is added to a customer's basket.  This could be "
#             "something like a personalised message to be printed on "
#             "a T-shirt."
#         ),
#     )

#     recommended_products = models.ManyToManyField(
#         "catalogue.Product",
#         through="ProductRecommendation",
#         blank=True,
#         verbose_name=_("Recommended products"),
#         help_text=_(
#             "These are products that are recommended to accompany the main product."
#         ),
#     )

#     # Denormalised product rating - used by reviews app.
#     # Product has no ratings if rating is None
#     rating = models.FloatField(_("Rating"), null=True, editable=False)

#     date_created = models.DateTimeField(
#         _("Date created"), auto_now_add=True, db_index=True
#     )

#     # This field is used by Haystack to reindex search
#     date_updated = models.DateTimeField(_("Date updated"), auto_now=True, db_index=True)

#     categories = models.ManyToManyField(
#         "catalogue.Category", through="ProductCategory", verbose_name=_("Categories")
#     )

#     #: Determines if a product may be used in an offer. It is illegal to
#     #: discount some types of product (e.g. ebooks) and this field helps
#     #: merchants from avoiding discounting such products
#     #: Note that this flag is ignored for child products; they inherit from
#     #: the parent product.
#     is_discountable = models.BooleanField(
#         _("Is discountable?"),
#         default=True,
#         help_text=_(
#             "This flag indicates if this product can be used in an offer or not"
#         ),
#     )

#     objects = ProductQuerySet.as_manager()

#     class Meta:
#         abstract = True
#         app_label = "catalogue"
#         ordering = ["-date_created"]
#         verbose_name = _("Product")
#         verbose_name_plural = _("Products")

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.attr = ProductAttributesContainer(product=self)

#     def __str__(self):
#         if self.title:
#             return self.title
#         if self.attribute_summary:
#             return "%s (%s)" % (self.get_title(), self.attribute_summary)
#         else:
#             return self.get_title()

#     def get_absolute_url(self):
#         """
#         Return a product's absolute URL
#         """
#         return reverse(
#             "catalogue:detail", kwargs={"product_slug": self.slug, "pk": self.id}
#         )

#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.get_title())
#         super().save(*args, **kwargs)
#         self.attr.save()

#     def refresh_from_db(self, using=None, fields=None):
#         super().refresh_from_db(using, fields)
#         self.attr.invalidate()

#     # Properties
        
#     @property
#     def options(self):
#         """
#         Returns a set of all valid options for this product.
#         It's possible to have options product class-wide, and per product.
#         """
#         pclass_options = self.get_product_class().options.all()
#         return pclass_options | self.product_options.all()

#     @cached_property
#     def has_options(self):
#         # Extracting annotated value with number of product class options
#         # from product list queryset.
#         has_product_class_options = getattr(self, "has_product_class_options", None)
#         has_product_options = getattr(self, "has_product_options", None)
#         if has_product_class_options is not None and has_product_options is not None:
#             return has_product_class_options or has_product_options
#         return self.options.exists()

#     @property
#     def is_shipping_required(self):
#         return self.get_product_class().requires_shipping

#     @property
#     def has_stockrecords(self):
#         """
#         Test if this product has any stockrecords
#         """
#         if self.id:
#             return self.stockrecords.exists()
#         return False

#     @property
#     def num_stockrecords(self):
#         return self.stockrecords.count()

#     @property
#     def attribute_summary(self):
#         """
#         Return a string of all of a product's attributes
#         """
#         attributes = self.get_attribute_values()
#         pairs = [attribute.summary() for attribute in attributes]
#         return ", ".join(pairs)

#     def get_title(self):
#         """
#         Return a product's title or it's parent's title if it has no title
#         """
#         title = self.title
#         if not title and self.parent_id:
#             title = self.parent.title
#         return title

#     get_title.short_description = pgettext_lazy("Product title", "Title")

#     def get_meta_title(self):
#         title = self.meta_title
#         if not title and self.is_child:
#             title = self.parent.meta_title
#         return title or self.get_title()

#     get_meta_title.short_description = pgettext_lazy("Product meta title", "Meta title")

#     def get_meta_description(self):
#         meta_description = self.meta_description
#         if not meta_description and self.is_child:
#             meta_description = self.parent.meta_description
#         return meta_description or striptags(self.description)

#     get_meta_description.short_description = pgettext_lazy(
#         "Product meta description", "Meta description"
#     )

#     def get_product_class(self):
#         """
#         Return a product's item class. Child products inherit their parent's.
#         """
#         if self.is_child:
#             return self.parent.product_class
#         else:
#             return self.product_class

#     get_product_class.short_description = _("Product class")

#     @deprecated
#     def get_is_discountable(self):
#         """
#         It used to be that, :py:attr:`.is_discountable` couldn't be set individually for child
#         products; so they had to inherit it from their parent. This is nolonger the case because
#         ranges can include child products as well. That make this method useless.
#         """
#         return self.is_discountable

#     # pylint: disable=no-member
#     def get_categories(self):
#         """
#         Return a product's public categories or parent's if there is a parent product.
#         """
#         if self.is_child:
#             return self.parent.categories.browsable()
#         else:
#             return self.categories.browsable()

#     get_categories.short_description = _("Categories")

#     def get_attribute_values(self):
#         if not self.pk:
#             return self.attribute_values.model.objects.none()

#         attribute_values = self.attribute_values.all()
#         if self.is_child:
#             parent_attribute_values = self.parent.attribute_values.exclude(
#                 attribute__code__in=attribute_values.values("attribute__code")
#             )
#             return attribute_values | parent_attribute_values

#         return attribute_values

#     # Images

#     def get_missing_image(self):
#         """
#         Returns a missing image object.
#         """
#         # This class should have a 'name' property so it mimics the Django file
#         # field.
#         return MissingProductImage()

#     # pylint: disable=no-member
#     def get_all_images(self):
#         if self.is_child and not self.images.exists() and self.parent_id is not None:
#             return self.parent.images.all()
#         return self.images.all()

#     def primary_image(self):
#         """
#         Returns the primary image for a product. Usually used when one can
#         only display one product image, e.g. in a list of products.
#         """
#         images = self.get_all_images()
#         ordering = self.images.model.Meta.ordering
#         if not ordering or ordering[0] != "display_order":
#             # Only apply order_by() if a custom model doesn't use default
#             # ordering. Applying order_by() busts the prefetch cache of
#             # the ProductManager
#             images = images.order_by("display_order")
#         try:
#             return images[0]
#         except IndexError:
#             # We return a dict with fields that mirror the key properties of
#             # the ProductImage class so this missing image can be used
#             # interchangeably in templates.  Strategy pattern ftw!
#             missing_image = self.get_missing_image()
#             return {"original": missing_image.name, "caption": "", "is_missing": True}

#     # Updating methods

#     def update_rating(self):
#         """
#         Recalculate rating field
#         """
#         self.rating = self.calculate_rating()
#         self.save()

#     update_rating.alters_data = True

#     # pylint: disable=no-member
#     def calculate_rating(self):
#         """
#         Calculate rating value
#         """
#         result = self.reviews.filter(status=self.reviews.model.APPROVED).aggregate(
#             sum=Sum("score"), count=Count("id")
#         )
#         reviews_sum = result["sum"] or 0
#         reviews_count = result["count"] or 0
#         rating = None
#         if reviews_count > 0:
#             rating = float(reviews_sum) / reviews_count
#         return rating

#     def has_review_by(self, user):
#         if user.is_anonymous:
#             return False
#         return self.reviews.filter(user=user).exists()

#     def is_review_permitted(self, user):
#         """
#         Determines whether a user may add a review on this product.

#         Default implementation respects OSCAR_ALLOW_ANON_REVIEWS and only
#         allows leaving one review per user and product.

#         Override this if you want to alter the default behaviour; e.g. enforce
#         that a user purchased the product to be allowed to leave a review.
#         """
#         if user.is_authenticated or settings.OSCAR_ALLOW_ANON_REVIEWS:
#             return not self.has_review_by(user)
#         else:
#             return False

#     @cached_property
#     def num_approved_reviews(self):
#         return self.reviews.approved().count()

#     @property
#     def sorted_recommended_products(self):
#         """Keeping order by recommendation ranking."""
#         return [
#             r.recommendation
#             for r in self.primary_recommendations.select_related("recommendation").all()
#         ]
