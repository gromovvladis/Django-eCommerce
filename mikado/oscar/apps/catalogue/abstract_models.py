import logging
import os
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.finders import find
from django.core.cache import cache
from django.core.exceptions import (
    ImproperlyConfigured,
    ValidationError,
    ObjectDoesNotExist,
)
from django.core.files.base import File
from django.db import models
from django.db.models import Count, Exists, OuterRef, Sum
from django.db.models.fields import Field
from django.db.models.lookups import StartsWith
from django.template.defaultfilters import striptags
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from treebeard.mp_tree import MP_Node

from oscar.core.loading import get_class, get_classes, get_model
from oscar.core.utils import get_default_currency, slugify
from oscar.models.fields import AutoSlugField, NullCharField
from oscar.models.fields.slugfield import SlugField
from oscar.utils.models import get_image_upload_path

CategoryQuerySet, ProductQuerySet, AdditionalQuerySet = get_classes(
    "catalogue.managers", ["CategoryQuerySet", "ProductQuerySet", "AdditionalQuerySet"]
)
ProductAttributesContainer = get_class(
    "catalogue.product_attributes", "ProductAttributesContainer"
)


# pylint: disable=abstract-method
class ReverseStartsWith(StartsWith):
    """
    Adds a new lookup method to the django query language, that allows the
    following syntax::

        henk__rstartswith="koe"

    The regular version of startswith::

        henk__startswith="koe"

     Would be about the same as the python statement::

        henk.startswith("koe")

    ReverseStartsWith will flip the right and left hand side of the expression,
    effectively making this the same query as::

    "koe".startswith(henk)
    """

    def process_rhs(self, qn, connection):
        return super().process_lhs(qn, connection)

    def process_lhs(self, compiler, connection, lhs=None):
        if lhs is not None:
            raise Exception("Flipped process_lhs does not accept lhs argument")
        return super().process_rhs(compiler, connection)


Field.register_lookup(ReverseStartsWith, "rstartswith")


class AbstractProductClass(models.Model):
    """
    Used for defining options and attributes for a subset of products.
    E.g. Books, DVDs and Toys. A product can only belong to one product class.

    At least one product class must be created when setting up a new
    Oscar deployment.

    Not necessarily equivalent to top-level categories but usually will be.
    """

    name = models.CharField("Имя", max_length=128)
    slug = AutoSlugField("Ярлык", max_length=128, unique=True, populate_from="name")

    #: Some product type don't require shipping (e.g. digital products) - we use
    #: this field to take some shortcuts in the checkout.
    requires_shipping = models.BooleanField("Доставка необходима?", default=True)

    #: Digital products generally don't require their stock levels to be
    #: tracked.
    track_stock = models.BooleanField("Отслеживать запасы", default=True)

    #: These are the options (set by the user when they add to basket) for this
    #: item class.  For instance, a product class of "SMS message" would always
    #: require a message to be specified before it could be bought.
    #: Note that you can also set options on a per-product level.
    options = models.ManyToManyField(
        "catalogue.Option", blank=True, verbose_name="Опция"
    )

    class_additionals = models.ManyToManyField(
        "catalogue.Additional",
        through="ProductAdditional",
        blank=True,
        verbose_name="Дополнительные товары класса",
        help_text=(
            "Дополнительные товары для всех продуктов этого класса"
        ),
    )

    class Meta:
        abstract = True
        app_label = "catalogue"
        ordering = ["name"]
        verbose_name = "Класс товара"
        verbose_name_plural = "Классы товара"

    def __str__(self):
        return self.name or self.slug

    @property
    def has_attributes(self):
        return self.attributes.exists()

    @property
    def products_count(self):
        return self.products.count()

    @property
    def get_options(self):
        return self.options.all()
    
    @property
    def get_additionals(self):
        return self.class_additionals.all()


class AbstractCategory(MP_Node):
    """
    A product category. Merely used for navigational purposes; has no
    effects on business logic.

    Uses :py:mod:`django-treebeard`.
    """

    #: Allow comparison of categories on a limited number of fields by ranges.
    #: When the Category model is overwritten to provide CMS content, defining
    #: this avoids fetching a lot of unneeded extra data from the database.
    COMPARISON_FIELDS = ("pk", "path", "depth")

    name = models.CharField("Имя", max_length=255, db_index=True)
    code = NullCharField(
        "Код",
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )
    description = models.TextField("Описание", blank=True)
    meta_title = models.CharField(
        "Мета заголовок", max_length=255, blank=True, null=True
    )
    meta_description = models.TextField("Мета описание", blank=True, null=True)
    image = models.ImageField(
        "Изображение", upload_to="categories", blank=True, null=True
    )
    slug = SlugField("Ярлык", max_length=255, db_index=True, unique=True)

    order = models.IntegerField("Порядок", default=0, null=False, blank=False)

    is_public = models.BooleanField(
        "Является общедоступным",
        default=True,
        db_index=True,
        help_text="Показывать эту категорию в результатах поиска и каталогах.",
    )

    is_promo = models.BooleanField(
        "Является промо-категорией в списке категорий",
        default=False,
        help_text="Показывать эту категорию в списке категорий, как промокатегорию ('Хиты' или 'Новинки')",
    )

    ancestors_are_public = models.BooleanField(
        "Категории предков являются общедоступными",
        default=True,
        db_index=True,
        help_text="Предки этой категории являются общедоступными",
    )

    _slug_separator = "/"
    _full_name_separator = " > "

    objects = CategoryQuerySet.as_manager()

    def __str__(self):
        return self.full_name
    
    
    # Images
    
    @cached_property
    def primary_image(self):
        """
        Returns the primary image for a product. Usually used when one can
        only display one product image, e.g. in a list of products.
        """
        img = self.image
        if not img:
            mis_img = MissingProductImage()
            return {"original": mis_img.name, "caption": "", "is_missing": True}

        return {"original": img.name, "caption": "", "is_missing": False}

    @property
    def full_name(self):
        """
        Returns a string representation of the category and it's ancestors,
        e.g. 'Books > Non-fiction > Essential programming'.

        It's rarely used in Oscar, but used to be stored as a CharField and is
        hence kept for backwards compatibility. It's also sufficiently useful
        to keep around.
        """
        names = [category.name for category in self.get_ancestors_and_self()]
        return self._full_name_separator.join(names)

    def get_full_slug(self, parent_slug=None):
        if self.is_root():
            return self.slug

        cache_key = self.get_url_cache_key()
        full_slug = cache.get(cache_key)
        if full_slug is None:
            parent_slug = (
                parent_slug if parent_slug is not None else self.get_parent().full_slug
            )
            full_slug = "%s%s%s" % (parent_slug, self._slug_separator, self.slug)
            cache.set(cache_key, full_slug)

        return full_slug

    @property
    def full_slug(self):
        """
        Returns a string of this category's slug concatenated with the slugs
        of it's ancestors, e.g. 'books/non-fiction/essential-programming'.

        Oscar used to store this as in the 'slug' model field, but this field
        has been re-purposed to only store this category's slug and to not
        include it's ancestors' slugs.
        """
        return self.get_full_slug()

    def generate_slug(self):
        """
        Generates a slug for a category. This makes no attempt at generating
        a unique slug.
        """
        return slugify(self.name)

    def save(self, *args, **kwargs):
        """
        Oscar traditionally auto-generated slugs from names. As that is
        often convenient, we still do so if a slug is not supplied through
        other means. If you want to control slug creation, just create
        instances with a slug already set, or expose a field on the
        appropriate forms.
        """
        if not self.slug:
            self.slug = self.generate_slug()
        super().save(*args, **kwargs)

    def set_ancestors_are_public(self):
        # Update ancestors_are_public for the sub tree.
        # note: This doesn't trigger a new save for each instance, rather
        # just a SQL update.
        included_in_non_public_subtree = self.__class__.objects.filter(
            is_public=False,
            path__rstartswith=OuterRef("path"),
            depth__lt=OuterRef("depth"),
        )
        self.get_descendants_and_self().update(
            ancestors_are_public=~Exists(included_in_non_public_subtree.values("id"))
        )

        # Correctly populate ancestors_are_public
        self.refresh_from_db()

    @classmethod
    def fix_tree(cls, destructive=False, fix_paths=False):
        super().fix_tree(destructive, fix_paths)
        for node in cls.get_root_nodes():
            # ancestors_are_public *must* be True for root nodes, or all trees
            # will become non-public
            if not node.ancestors_are_public:
                node.ancestors_are_public = True
                node.save()
            else:
                node.set_ancestors_are_public()

    def get_meta_title(self):
        return self.meta_title or self.name

    def get_meta_description(self):
        return self.meta_description or striptags(self.description)

    def get_ancestors_and_self(self):
        """
        Gets ancestors and includes itself. Use treebeard's get_ancestors
        if you don't want to include the category itself. It's a separate
        function as it's commonly used in templates.
        """
        if self.is_root():
            return [self]

        return list(self.get_ancestors()) + [self]

    def get_descendants_and_self(self):
        """
        Gets descendants and includes itself. Use treebeard's get_descendants
        if you don't want to include the category itself. It's a separate
        function as it's commonly used in templates.
        """
        return self.get_tree(self)

    def get_url_cache_key(self):
        # current_locale = get_language()
        # cache_key = "CATEGORY_URL_%s_%s" % (current_locale, self.pk)
        cache_key = "CATEGORY_URL_%s" % (self.pk)
        return cache_key

    def _get_absolute_url(self, parent_slug=None):
        """
        Our URL scheme means we have to look up the category's ancestors. As
        that is a bit more expensive, we cache the generated URL. That is
        safe even for a stale cache, as the default implementation of
        ProductCategoryView does the lookup via primary key anyway. But if
        you change that logic, you'll have to reconsider the caching
        approach.
        """
        return reverse(
            "catalogue:category",
            kwargs={
                "category_slug": self.get_full_slug(parent_slug=parent_slug),
            },
        )

    def get_absolute_url(self):
        return self._get_absolute_url()

    class Meta:
        abstract = True
        app_label = "catalogue"
        ordering = ["order","path"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def has_children(self):
        return self.get_num_children() > 0

    def get_num_children(self):
        return self.get_children().count()
    
    def get_num_products(self):
        cats = self
        cats_list = []

        if self.has_children():
            cats = self.get_ancestors_and_self()
            for cat in cats:
                cats_list.append(cat.id)
        else: 
            cats_list.append(cats.id)
  
        Product = get_model('catalogue', 'Product')
        prod_nums = Product.objects.filter(categories__in=cats_list).count()

        return prod_nums



class AbstractProductCategory(models.Model):
    """
    Joining model between products and categories. Exists to allow customising.
    """

    product = models.ForeignKey(
        "catalogue.Product", on_delete=models.CASCADE, verbose_name="Продукт"
    )
    category = models.ForeignKey(
        "catalogue.Category", on_delete=models.CASCADE, verbose_name="Категория"
    )

    class Meta:
        abstract = True
        app_label = "catalogue"
        ordering = ["product", "category"]
        unique_together = ("product", "category")
        verbose_name = "Категория товара"
        verbose_name_plural = "Категории товара"

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
        (STANDALONE, "Простой товар"),
        (PARENT, "Вариативный товар"),
        (CHILD, "Вариация"),
    )
    structure = models.CharField(
        "Вид продукта",
        max_length=10,
        choices=STRUCTURE_CHOICES,
        default=STANDALONE,
    )

    is_public = models.BooleanField(
        "Является общедоступным",
        default=True,
        db_index=True,
        help_text="Показывать этот продукт в результатах поиска и каталогах.",
    )

    upc = NullCharField(
        "Товарный код продукта UPC",
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        help_text=(
            "Универсальный код продукта (UPC) является идентификатором для "
            "продукта, который не является специфичным для конкретного"
            "Поставщик. Например, ISBN книги"
        ),
    )

    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="children",
        verbose_name="Вариативный товар",
        help_text=(
            "Выбирайте родительский продукт только в том случае, если вы создаете дочерний "
            "товар. Например, если это размер "
            "4 конкретной футболки. Оставьте пустым, если это "
            "автономный продукт (т.е. существует только одна версия"
            " этого продукта)."
        ),
    )

    # Title is mandatory for canonical products but optional for child products
    title = models.CharField(("Название продукта", "Название"), max_length=255, blank=True
    )
    variant = models.CharField(("Название варианта", "Вариант"), max_length=255, blank=True
    )

    slug = SlugField("Ярлык", max_length=255, unique=True)
    description = models.TextField("Описание", blank=True)
    short_description = models.CharField("Краткое описание", max_length=255, null=True, blank=True)

    meta_title = models.CharField(
        "Мета заголовок", max_length=255, blank=True, null=True
    )
    meta_description = models.TextField("Мета описание", blank=True, null=True)

    #: "Kind" of product, e.g. T-Shirt, Book, etc.
    #: None for child products, they inherit their parent's product class
    product_class = models.ForeignKey(
        "catalogue.ProductClass",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name="Тип продукта",
        related_name="products",
        help_text="Выберите, что это за продукт",
    )
    attributes = models.ManyToManyField(
        "catalogue.ProductAttribute",
        through="ProductAttributeValue",
        verbose_name="Атрибуты",
        help_text=(
            "Атрибут продукта — это то, что этот продукт может"
            "иметь, например, размер, указанный его классом"
        ),
    )
    #: It's possible to have options product class-wide, and per product.
    product_options = models.ManyToManyField(
        "catalogue.Option",
        blank=True,
        verbose_name="Опции продукта",
        help_text=(
            "Параметры — это значения, которые могут быть связаны с элементом, "
            "когда товар добавляется в корзину покупателя. Это может быть "
            "что-то вроде персонализированного сообщения для печати на футболке"
        ),
    )

    product_additionals = models.ManyToManyField(
        "catalogue.Additional",
        through="ProductAdditional",
        blank=True,
        verbose_name="Дополнительные товары продукта",
        help_text=(
            "Доп товары"
        ),
    )

    recommended_products = models.ManyToManyField(
        "catalogue.Product",
        through="ProductRecommendation",
        blank=True,
        verbose_name="Рекомендуемые продукты",
        help_text=(
            "Это продукты, которые рекомендуется сопровождать основной продукт."
        ),
    )

    # Denormalised product rating - used by reviews app.
    # Product has no ratings if rating is None
    rating = models.FloatField("Рейтинг", null=True, editable=False)

    order = models.IntegerField("Порядок", null=False, blank=False, default=0)
    
    cooking_time = models.IntegerField("Время приготовления", null=False, blank=False, default=20)

    date_created = models.DateTimeField(
        "Дата создания", auto_now_add=True, db_index=True
    )

    # This field is used by Haystack to reindex search
    date_updated = models.DateTimeField("Дата изменения", auto_now=True, db_index=True)

    categories = models.ManyToManyField(
        "catalogue.Category", through="ProductCategory", verbose_name="Категории"
    )

    #: Determines if a product may be used in an offer. It is illegal to
    #: discount some types of product (e.g. ebooks) and this field helps
    #: merchants from avoiding discounting such products
    #: Note that this flag is ignored for child products; they inherit from
    #: the parent product.
    is_discountable = models.BooleanField(
        "Предоставляется скидка?",
        default=True,
        help_text=(
            "Этот флаг указывает, можно ли использовать этот продукт в предложении со скидками или нет"
        ),
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        abstract = True
        app_label = "catalogue"
        ordering = ["-order"]
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

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
        Return a product's variant absolute URL
        """

        if self.is_child:
            slug = self.parent.slug
            cat = self.parent.categories.first().full_slug
        else:
            slug = self.slug
            cat = self.categories.first().full_slug

        return reverse(
            "catalogue:detail", kwargs={"product_slug": slug, "category_slug": cat}
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
            raise ValidationError("Ваш продукт должен иметь название.")
        if not self.product_class:
            raise ValidationError("Ваш продукт должен иметь класс продукта.")
        if self.parent_id:
            raise ValidationError("Родительский продукт может иметь только дочерний продукт.")

    def _clean_child(self):
        """
        Validates a child product
        """
        has_parent = self.parent or self.parent_id

        if not has_parent:
            raise ValidationError("Дочернему продукту нужен родительский продукт.")
        if has_parent and not self.parent.is_parent:
            raise ValidationError("Вы можете назначать только дочерние продукты родительским продуктам.")
        if self.product_class:
            raise ValidationError("Дочерний продукт не может иметь класс продукта.")
        if self.pk and self.categories.exists():
            raise ValidationError("Дочернему товару не может быть присвоена категория.")
        # Note that we only forbid options on product level
        if self.pk and self.product_options.exists():
            raise ValidationError("У дочернего продукта не может быть опций.")

    def _clean_parent(self):
        """
        Validates a parent product.
        """
        self._clean_standalone()
        if self.has_stockrecords:
            raise ValidationError("Родительский продукт не может иметь складские записи.")

    def save(self, *args, **kwargs):
        if not self.slug:
            if self.is_child and not self.title:
                self.slug = slugify(self.get_title() + self.variant)
            else:
                self.slug = slugify(self.get_title())

        super().save(*args, **kwargs)
        self.attr.save()

    def refresh_from_db(self, using=None, fields=None):
        super().refresh_from_db(using, fields)
        self.attr.invalidate()

    # Properties

    @cached_property
    def is_standalone(self):
        return self.structure == self.STANDALONE

    @cached_property
    def is_parent(self):
        return self.structure == self.PARENT

    @cached_property
    def is_child(self):
        return self.structure == self.CHILD

    def can_be_parent(self, give_reason=False):
        """
        Helps decide if a the product can be turned into a parent product.
        """
        reason = None
        if self.is_child:
            reason = "Указанный родительский продукт является дочерним продуктом."
        if self.has_stockrecords:
            reason = "Невозможно добавить дочерний продукт к продукту с учетными записями на складе."
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
        return self.get_product_class().options.all() | self.product_options.all()
    
    @property
    def additionals(self):
        """
        Returns a set of all additionals for this product.
        """
        return self.get_product_class().class_additionals.all() | self.product_additionals.all()

    @cached_property
    def has_options(self):
        # Extracting annotated value with number of product class options
        # from product list queryset.
        # has_product_class_options = getattr(self, "has_product_class_options", None)
        # has_product_options = getattr(self, "has_product_options", None)
        # if has_product_class_options is not None and has_product_options is not None:
        #     return has_product_class_options or has_product_options
        
        options = self.options.all()
        if options:
            return True
        return False
    
    @cached_property
    def has_additions(self):
        # Extracting annotated value with number of product class options
        # from product list queryset.
        # has_product_class_additionals = getattr(self, "has_product_class_additionals", None)
        # has_product_additionals = getattr(self, "has_product_additionals", None)
        # if has_product_class_additionals is not None and has_product_additionals is not None:
        #     return has_product_class_additionals or has_product_additionals
        
        additionals = self.additionals.all()
        if additionals:
            return True
        return False
    
    # @cached_property
    # def has_compound(self):
    #     compound = self.attributes.filter(code='compound')
    #     if compound:
    #         return True
    #     return False
    
    # @property
    # def compound(self):
        # return self.attribute_values.filter(attribute__code='compound').first().value_as_text

    @cached_property
    def has_weight(self):
        if self.attributes.filter(code='weight'):
            return True
        return False
    

    @property
    def weight(self):
        return self.attribute_values.get(attribute__code='weight').value
    
    @property
    def short_desc(self):
        return self.short_description
    
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

    def get_prices(self):
        """
        Get list of stockrecord prices
        """
        prices = []
        stockrecords = []

        if self.id:

            if self.is_parent:
                childs = self.children.all()
                for child in childs:
                    stockrecords += child.stockrecords.values_list('price')
            else: 
                stockrecords += self.stockrecords.values_list('price')

            if stockrecords:
                for stc in stockrecords:
                    prices.append(stc[0])

                prices = set([min(prices), max(prices)])

        return prices
    
    def get_low_price(self):
        return self.get_prices().pop() if self.get_prices().pop() else None

    def get_title(self):
        """
        Return a product's title or it's parent's title if it has no title
        """
        title = self.title
        if not title and self.parent_id:
            title = self.parent.title
        return title
    
    def get_variant(self):
        """
        Return a product's title or it's parent's title if it has no title
        """
        variant = self.variant
        if not variant and self.parent_id:
            if self.title:
                return self.title
            return self.parent.title
        return variant

    get_title.short_description = ("Название продукта", "Название")

    def get_meta_title(self):
        title = self.meta_title
        if not title and self.is_child:
            title = self.parent.meta_title
        return title or self.get_title()

    get_meta_title.short_description = ("Мета-заголовок продукта", "Мета-заголовок")

    def get_meta_description(self):
        meta_description = self.meta_description
        if not meta_description and self.is_child:
            meta_description = self.parent.meta_description
        return meta_description or striptags(self.description)

    get_meta_description.short_description = (
        "Мета-описание продукта", "Мета-описание"
    )

    def get_product_class(self):
        """
        Return a product's item class. Child products inherit their parent's.
        """
        if self.is_child:
            return self.parent.product_class
        else:
            return self.product_class

    get_product_class.short_description = "Класс товара"

    # pylint: disable=no-member
    def get_categories(self):
        """
        Return a product's public categories or parent's if there is a parent product.
        """
        if self.is_child:
            return self.parent.categories.browsable()
        else:
            return self.categories.browsable()

    get_categories.short_description = "Категории"

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
        if user.is_authenticated:
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


class AbstractProductRecommendation(models.Model):
    """
    'Through' model for product recommendations
    """

    primary = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="primary_recommendations",
        verbose_name="Основной продукт",
    )
    recommendation = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        verbose_name="Рекомендуемый продукт",
    )
    ranking = models.PositiveSmallIntegerField(
        "Рейтинг",
        default=0,
        db_index=True,
        help_text=(
            "Определяет порядок товаров. Товар с более высоким значением"
            "Значение появится перед значением с более низким рейтингом."
        ),
    )

    class Meta:
        abstract = True
        app_label = "catalogue"
        ordering = ["primary", "-ranking"]
        unique_together = ("primary", "recommendation")
        verbose_name = "Рекомендация продукта"
        verbose_name_plural = "Рекомендации продукта"


class AbstractProductAttribute(models.Model):
    """
    Defines an attribute for a product class. (For example, number_of_pages for
    a 'book' class)
    """

    product_class = models.ForeignKey(
        "catalogue.ProductClass",
        blank=True,
        on_delete=models.CASCADE,
        related_name="attributes",
        null=True,
        verbose_name="Тип продукта",
    )
    name = models.CharField("Имя", max_length=128)
    code = models.SlugField(
        "Код",
        max_length=128,
        unique=True
    )

    # Attribute types
    TEXT = "text"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    FLOAT = "float"
    RICHTEXT = "richtext"
    OPTION = "option"
    MULTI_OPTION = "multi_option"
    FILE = "file"
    IMAGE = "image"
    TYPE_CHOICES = (
        (TEXT, "Текст"),
        (INTEGER, "Целое число"),
        (BOOLEAN, "Да / Нет"),
        (FLOAT, "Дробное число"),
        (RICHTEXT, "Текстовое поле"),
        (OPTION, "Опция"),
        (MULTI_OPTION, "Мульти-опция"),
        (FILE, "Файл"),
        (IMAGE, "Изображение"),
    )
    type = models.CharField(
        choices=TYPE_CHOICES,
        default=TYPE_CHOICES[0][0],
        max_length=20,
        verbose_name="Тип",
    )

    option_group = models.ForeignKey(
        "catalogue.AttributeOptionGroup",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="product_attributes",
        verbose_name="Группа опций",
        help_text='Выберите группу параметров, если используете тип «Опция» или «Множество опций».',
    )
    required = models.BooleanField("Необходимый", default=False)

    class Meta:
        abstract = True
        app_label = "catalogue"
        ordering = ["code"]
        verbose_name = "Атрибут продукта"
        verbose_name_plural = "Атрибуты продукта"
        unique_together = ("code", "product_class")

    @property
    def is_option(self):
        return self.type == self.OPTION

    @property
    def is_multi_option(self):
        return self.type == self.MULTI_OPTION

    @property
    def is_file(self):
        return self.type in [self.FILE, self.IMAGE]

    def __str__(self):
        return self.name

    def clean(self):
        if self.type == self.BOOLEAN and self.required:
            raise ValidationError("Логический атрибут не должен быть обязательным.")

    def _get_value_obj(self, product, value):
        try:
            return product.attribute_values.get(attribute=self)
        except ObjectDoesNotExist:
            # FileField uses False for announcing deletion of the file
            # not creating a new value
            delete_file = self.is_file and value is False
            if value is None or value == "" or delete_file:
                return None
            return product.attribute_values.create(attribute=self)

    def _bind_value_file(self, value_obj, value):
        if value is None:
            # No change
            return value_obj
        elif value is False:
            return None
        else:
            # New uploaded file
            value_obj.value = value
            return value_obj

    def _bind_value_multi_option(self, value_obj, value):
        # ManyToMany fields are handled separately
        if value is None:
            return None
        try:
            count = value.count()
        except (AttributeError, TypeError):
            count = len(value)
        if count == 0:
            return None
        else:
            value_obj.value = value
            return value_obj

    def _bind_value(self, value_obj, value):
        if value is None or value == "":
            return None
        value_obj.value = value
        return value_obj

    def bind_value(self, value_obj, value):
        """
        bind_value will bind the value passed to the value_obj, if the bind_value
        return None, that means the value_obj is supposed to be deleted.
        """
        if self.is_file:
            return self._bind_value_file(value_obj, value)
        elif self.is_multi_option:
            return self._bind_value_multi_option(value_obj, value)
        else:
            return self._bind_value(value_obj, value)

    def save_value(self, product, value):
        value_obj = self._get_value_obj(product, value)

        if value_obj is None:
            return None

        updated_value_obj = self.bind_value(value_obj, value)
        if updated_value_obj is None:
            value_obj.delete()
        elif updated_value_obj.is_dirty:
            updated_value_obj.save()

        return updated_value_obj

    def validate_value(self, value):
        validator = getattr(self, "_validate_%s" % self.type)
        validator(value)

    # Validators

    def _validate_text(self, value):
        if not isinstance(value, str):
            raise ValidationError("Должно быть строка")

    _validate_richtext = _validate_text

    def _validate_float(self, value):
        try:
            float(value)
        except ValueError:
            raise ValidationError("Должно быть числом с плавающей запятой")

    def _validate_integer(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError("Должно быть целое число")

    def _validate_boolean(self, value):
        if not type(value) == bool:
            raise ValidationError("Должно быть логическое значение ДА / НЕТ")

    def _validate_multi_option(self, value):
        try:
            values = iter(value)
        except TypeError:
            raise ValidationError("Должен быть списком или набором запросов AttributeOption.")
        # Validate each value as if it were an option
        # Pass in valid_values so that the DB isn't hit multiple times per iteration
        valid_values = self.option_group.options.values_list("option", flat=True)
        for value in values:
            self._validate_option(value, valid_values=valid_values)

    def _validate_option(self, value, valid_values=None):
        if not isinstance(value, get_model("catalogue", "AttributeOption")):
            raise ValidationError("Должен быть экземпляром объекта модели AttributeOption.")
        if not value.pk:
            raise ValidationError("AttributeOption еще не сохранен.")
        if valid_values is None:
            valid_values = self.option_group.options.values_list("option", flat=True)
        if value.option not in valid_values:
            raise ValidationError(
                ("%(enum)s не корректен для %(attr)s")
                % {"enum": value, "attr": self}
            )

    def _validate_file(self, value):
        if value and not isinstance(value, File):
            raise ValidationError("Должно быть поле файла")

    _validate_image = _validate_file


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
        verbose_name="Атрибут",
    )
    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="attribute_values",
        verbose_name="Продукт",
    )

    value_text = models.TextField("Текст", blank=True, null=True)
    value_integer = models.IntegerField(
        "Целое число", blank=True, null=True, db_index=True
    )
    value_boolean = models.BooleanField(
        "Логическое значение", blank=True, null=True, db_index=True
    )
    value_float = models.FloatField("Дробное число", blank=True, null=True, db_index=True)
    value_richtext = models.TextField("Текстовое поле", blank=True, null=True)
    value_multi_option = models.ManyToManyField(
        "catalogue.AttributeOption",
        blank=True,
        related_name="multi_valued_attribute_values",
        verbose_name="Значение нескольких вариантов Мульти-Опции",
    )
    value_option = models.ForeignKey(
        "catalogue.AttributeOption",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name="Вариант значения Опции",
    )
    value_file = models.FileField(
        upload_to=get_image_upload_path, max_length=255, blank=True, null=True
    )
    value_image = models.ImageField(
        upload_to=get_image_upload_path, max_length=255, blank=True, null=True
    )

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
        verbose_name = "Значение атрибута продукта"
        verbose_name_plural = "Значения атрибутов продукта"

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
            return ("Значение атрибута продукта", "Да")
        return ("Значение атрибута продукта", "Нет")

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


class AbstractAttributeOptionGroup(models.Model):
    """
    Defines a group of options that collectively may be used as an
    attribute type

    For example, Language
    """

    name = models.CharField("Имя", max_length=128)
    code = NullCharField(
        "Уникальный идентификатор",
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
        verbose_name = "Группа параметров атрибута"
        verbose_name_plural = "Группы параметров атрибутов"

    @property
    def option_summary(self):
        options = [o.option for o in self.options.all()]
        return ", ".join(options)


class AbstractAttributeOption(models.Model):
    """
    Provides an option within an option group for an attribute type
    Examples: In a Language group, English, Greek, French
    """

    group = models.ForeignKey(
        "catalogue.AttributeOptionGroup",
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Группа",
    )
    option = models.CharField("Опция", max_length=255)
    code = NullCharField(
        "Уникальный идентификатор",
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
        verbose_name = "Параметр атрибута"
        verbose_name_plural = "Параметры атрибута"


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
        (TEXT, "Текст"),
        (INTEGER, "Целое число"),
        (BOOLEAN, "Да / Нет"),
        (FLOAT, "Дробное число"),
        (SELECT, "Селект"),
        (RADIO, "Радио кнопка"),
        (MULTI_SELECT, "Multi select"),
        (CHECKBOX, "Флажок"),
        
    )

    empty_label = "------"
    empty_radio_label = "Пропустить этот вариант"

    name = models.CharField("Имя", max_length=128, db_index=True)
    code = AutoSlugField("Код", max_length=128, unique=True, populate_from="name")
    type = models.CharField(
        "Тип", max_length=255, default=TEXT, choices=TYPE_CHOICES
    )
    required = models.BooleanField("Обязательная ли эта опция?", default=False)
    option_group = models.ForeignKey(
        "catalogue.AttributeOptionGroup",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="product_options",
        verbose_name="Группа опций",
        help_text='Выберите группу параметров, если используете тип «Опция» или «Множество опций».',
    )
    help_text = models.CharField(
        verbose_name="Текст справки",
        blank=True,
        null=True,
        max_length=255,
        help_text="Текст справки, отображаемый пользователю в форме добавления в корзину",
    )
    order = models.IntegerField(
        "Порядок",
        null=True,
        blank=True,
        help_text="Управляет порядком опций продукта на страницах сведений о продукте.",
        db_index=True,
    )

    date_created = models.DateTimeField("Дата создания", auto_now_add=True)
    date_updated = models.DateTimeField("Дата изменения", auto_now=True, db_index=True)

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
                    ("Для типа требуется группа опций %s") % self.get_type_display()
                )
        elif self.option_group:
            raise ValidationError(
                ("Группа опций не может использоваться с типом %s") % self.get_type_display()
            )
        return super().clean()

    class Meta:
        abstract = True
        app_label = "catalogue"
        ordering = ["order", "name"]
        verbose_name = "Опция"
        verbose_name_plural = "Опиции"

    def __str__(self):
        return self.name



class AbstractProductAdditional(models.Model):
    """
    'Through' model for product additional
    """
    primary_class = models.ForeignKey(
        "catalogue.ProductClass",
        on_delete=models.CASCADE,
        # related_name="class_additionals",
        verbose_name="Основной класс",
        blank=True,
        null=True,
    )

    primary_product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        # related_name="product_additionals",
        verbose_name="Основной продукт",
        blank=True,
        null=True,
    )

    additional_product = models.ForeignKey(
        "catalogue.Additional",
        on_delete=models.CASCADE,
        # related_name="product_additional",
        verbose_name="Рекомендуемый продукт",
    )
    ranking = models.PositiveSmallIntegerField(
        "Порядок",
        default=0,
        db_index=True,
        help_text=(
            "Определяет порядок товаров. Товар с более высоким значением"
            "Значение появится перед значением с более низким рейтингом."
        ),
    )

    class Meta:
        abstract = True
        app_label = "catalogue"
        ordering = ["primary_class", "primary_product", "-ranking"]
        unique_together = ("primary_class", "primary_product", "additional_product")
        verbose_name = "Дополнительный товар"
        verbose_name_plural = "Дополнительные товары"



class AbstractAdditional(models.Model):
    """
    An additional that can be selected for a particular item when the product
    is added to the basket. 
    """

    name = models.CharField("Имя", max_length=128, db_index=True)
    code = AutoSlugField("Код", max_length=128, unique=True, populate_from="name")
    upc = models.CharField("Уникальный код товара в базе", max_length=128, unique=True)

    order = models.IntegerField(
        "Порядок",
        null=True,
        blank=True,
        help_text="Управляет порядком опций продукта на страницах сведений о продукте.",
    )

    is_public = models.BooleanField(
        "Является общедоступным",
        default=True,
        help_text="Показывать этот продукт в результатах поиска и каталогах.",
    )

    description = models.TextField("Описание", blank=True)

    price_currency = models.CharField(
        "Валюта", max_length=12, default=get_default_currency
    )
        
    price = models.DecimalField(
        "Цена",
        decimal_places=2,
        max_digits=12, 
        default=0,
        help_text="Цена продажи",
    )

    old_price = models.DecimalField(
        "Цена до скидки",
        decimal_places=2,
        max_digits=12, 
        blank=True,
        null=True,
        help_text="Цена до скидки. Оставить пустым, если скидки нет",
    )

    weight = models.IntegerField(
        "Вес",
        default=0,
        help_text="Вес дополнительного товара",
    )

    max_amount = models.IntegerField(
        "Максимальное количество",
        default=1,
        help_text="Максимальное количество доп. товара, которое может быть добавлено к основному товару",
    )

    img = models.ImageField(
        "Изображение", upload_to="additionals", blank=True, null=True, max_length=255
    )

    date_created = models.DateTimeField("Дата создания", auto_now_add=True)
    date_updated = models.DateTimeField("Дата изменения", auto_now=True, db_index=True)

    objects = AdditionalQuerySet.as_manager()

    @cached_property
    def primary_image(self):
        """
        Returns the primary image for a product. Usually used when one can
        only display one product image, e.g. in a list of products.
        """
        img = self.img
        if not img:
            return MissingProductImage()

        return img

    class Meta:
        abstract = True
        app_label = "catalogue"
        ordering = ["order", "name"]
        verbose_name = "Дополнительный товар"
        verbose_name_plural = "Дополнительные товары"

    def __str__(self):
        return self.name


class MissingProductImage(object):
    """
    Mimics a Django file field by having a name property.

    :py:mod:`sorl-thumbnail` requires all it's images to be in MEDIA_ROOT. This class
    tries symlinking the default "missing image" image in STATIC_ROOT
    into MEDIA_ROOT for convenience, as that is necessary every time an Oscar
    project is setup. This avoids the less helpful NotFound IOError that would
    be raised when :py:mod:`sorl-thumbnail` tries to access it.
    """

    def __init__(self, name=None):
        self.name = name if name else settings.OSCAR_MISSING_IMAGE_URL
        media_file_path = os.path.join(settings.MEDIA_ROOT, self.name)
        # don't try to symlink if MEDIA_ROOT is not set (e.g. running tests)
        if settings.MEDIA_ROOT and not os.path.exists(media_file_path):
            self.symlink_missing_image(media_file_path)

    def symlink_missing_image(self, media_file_path):
        static_file_path = find("oscar/img/%s" % self.name)
        if static_file_path is not None:
            try:
                # Check that the target directory exists, and attempt to
                # create it if it doesn't.
                media_file_dir = os.path.dirname(media_file_path)
                if not os.path.exists(media_file_dir):
                    os.makedirs(media_file_dir)
                os.symlink(static_file_path, media_file_path)
            except OSError:
                raise ImproperlyConfigured(
                    (
                        "Please copy/symlink the "
                        "'missing image' image at %s into your MEDIA_ROOT at %s. "
                        "This exception was raised because Oscar was unable to "
                        "symlink it for you."
                    )
                    % (static_file_path, settings.MEDIA_ROOT),
                )
            else:
                logging.info(
                    (
                        "Symlinked the 'missing image' image at %s into your "
                        "MEDIA_ROOT at %s"
                    ),
                    static_file_path,
                    settings.MEDIA_ROOT,
                )


class AbstractProductImage(models.Model):
    """
    An image of a product
    """

    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Продукт",
    )
    code = NullCharField(
        "Код",
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )
    original = models.ImageField(
        "Оригинал", upload_to=get_image_upload_path, max_length=255
    )
    caption = models.CharField("Подпись", max_length=200, blank=True)

    #: Use display_order to determine which is the "primary" image
    display_order = models.PositiveIntegerField(
        "Порядок отображения",
        default=0,
        db_index=True,
        help_text=(
            "Изображение с нулевым порядком отображения будет основным"
        ),
    )
    date_created = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        abstract = True
        app_label = "catalogue"
        # Any custom models should ensure that this ordering is unchanged, or
        # your query count will explode. See AbstractProduct.primary_image.
        ordering = ["display_order"]
        verbose_name = "Изображение продукта"
        verbose_name_plural = "Изображения продуктов"

    def __str__(self):
        return "Image of '%s'" % self.product

    def is_primary(self):
        """
        Return bool if image display order is 0
        """
        return self.display_order == 0

    def delete(self, *args, **kwargs):
        """
        Always keep the display_order as consecutive integers. This avoids
        issue #855.
        """
        super().delete(*args, **kwargs)
        for idx, image in enumerate(self.product.images.all()):
            image.display_order = idx
            image.save()
