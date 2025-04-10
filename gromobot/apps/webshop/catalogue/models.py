import uuid

from core.loading import get_class, get_classes, get_model
from core.models.fields import AutoSlugField, NullCharField, SlugField
from core.models.img.image_processor import ImageProcessor
from core.models.img.missing_image import MissingImage
from core.models.img.paths import (
    get_image_additionals_upload_path,
    get_image_categories_upload_path,
    get_image_products_upload_path,
)
from core.utils import get_default_currency, slugify
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
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

CategoryQuerySet, ProductQuerySet, AdditionalQuerySet, AttributeQuerySet = get_classes(
    "webshop.catalogue.managers",
    ["CategoryQuerySet", "ProductQuerySet", "AdditionalQuerySet", "AttributeQuerySet"],
)
ProductAttributesContainer = get_class(
    "webshop.catalogue.product_attributes", "ProductAttributesContainer"
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


class ProductClass(models.Model):
    """
    Used for defining options and attributes for a subset of products.
    E.g. Books, DVDs and Toys. A product can only belong to one product class.

    At least one product class must be created when setting up a new
    Oscar deployment.

    Not necessarily equivalent to top-level categories but usually will be.
    """

    name = models.CharField("Имя", max_length=128)
    slug = AutoSlugField("Ярлык", max_length=128, unique=True, populate_from="name")
    EMPTY, PCS, KG, LITR, MLITR, METR, COMPLECT, UPAC, ED = (
        "",
        "шт",
        "кг",
        "л",
        "мл",
        "м",
        "компл",
        "упак",
        "ед",
    )
    MEASURE_CHOICES = (
        (EMPTY, "Не задано"),
        (PCS, "шт - штуки"),
        (KG, "кг - килограммы"),
        (LITR, "л - литры"),
        (MLITR, "мл - миллилитры"),
        (METR, "м - метры"),
        (COMPLECT, "компл - комплекты"),
        (UPAC, "упак - упаковки"),
        (ED, "ед - единицы"),
    )
    measure_name = models.CharField(
        "Единицы изменения",
        max_length=128,
        null=False,
        choices=MEASURE_CHOICES,
        default=EMPTY,
    )

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
        help_text=("Дополнительные товары для всех товаров этого класса"),
    )
    class_attributes = models.ManyToManyField(
        "catalogue.Attribute",
        through="ProductAttribute",
        blank=True,
        verbose_name="Атрибуты класса",
        help_text=("Атрибуты для всех товаров этого класса"),
    )

    class Meta:
        app_label = "catalogue"
        ordering = ["name"]
        verbose_name = "Класс товара"
        verbose_name_plural = "Классы товара"

    def __str__(self):
        return self.name or self.slug

    @property
    def has_attributes(self):
        return self.class_attributes.exists()

    @property
    def has_additionals(self):
        return self.class_additionals.exists()

    @property
    def get_options(self):
        return self.options.all()

    @property
    def get_additionals(self):
        return self.class_additionals.all()


class Category(MP_Node):
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
    description = models.TextField("Описание", blank=True)
    meta_title = models.CharField(
        "Мета заголовок", max_length=255, blank=True, null=True
    )
    meta_description = models.TextField("Мета описание", blank=True, null=True)
    image = models.ImageField(
        "Изображение", upload_to=get_image_categories_upload_path, blank=True, null=True
    )
    slug = SlugField("Ярлык", max_length=255, db_index=True, unique=True)
    order = models.IntegerField("Порядок", default=0, null=False, blank=False)
    is_public = models.BooleanField(
        "Является общедоступным",
        default=True,
        db_index=True,
        help_text="Показывать эту категорию в результатах поиска и каталогах.",
    )
    evotor_id = models.CharField(
        "ID Эвотор",
        max_length=128,
        blank=True,
        null=True,
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
        if not self.image:
            mis_img = MissingImage()
            return {"original": mis_img, "caption": self.name, "is_missing": True}

        return {"original": self.image, "caption": self.name, "is_missing": False}

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
        original_slug = slugify(self.name)
        slug = original_slug
        counter = 1

        # Проверка на уникальность slug
        while self.__class__.objects.filter(slug=slug).exclude(id=self.id).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        """
        Oscar traditionally auto-generated slugs from names. As that is
        often convenient, we still do so if a slug is not supplied through
        other means. If you want to control slug creation, just create
        instances with a slug already set, or expose a field on the
        appropriate forms.
        """
        if self.image:
            processor = ImageProcessor()
            optimized_image = processor.optimize_image(self.image)
            self.image.save(optimized_image.name, optimized_image, save=False)

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
        cache_key = "CATEGORY_URL_%s" % (self.pk)
        return cache_key

    def get_name(self):
        return self.name

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

    def get_evotor_parent_id(self):
        parent = self.get_parent()
        return parent.evotor_id if parent else ""

    def get_absolute_url(self):
        return self._get_absolute_url()

    def get_staff_url(self):
        """
        Return a category's absolute URL
        """
        return reverse("dashboard:catalogue-category-update", kwargs={"pk": self.id})

    class Meta:
        app_label = "catalogue"
        ordering = ["path", "order"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def has_children(self):
        return self.get_children_count() > 0


class ProductCategory(models.Model):
    """
    Joining model between products and categories. Exists to allow customising.
    """

    product = models.ForeignKey(
        "catalogue.Product", on_delete=models.CASCADE, verbose_name="Товар"
    )
    category = models.ForeignKey(
        "catalogue.Category", on_delete=models.CASCADE, verbose_name="Категория"
    )

    class Meta:
        app_label = "catalogue"
        ordering = ["product", "category"]
        unique_together = ("product", "category")
        verbose_name = "Категория товара"
        verbose_name_plural = "Категории товара"

    def __str__(self):
        return "<productcategory for product '%s'>" % self.product


class Product(models.Model):
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
        "Вид товара",
        max_length=10,
        choices=STRUCTURE_CHOICES,
        default=STANDALONE,
    )
    is_public = models.BooleanField(
        "Является общедоступным",
        default=True,
        db_index=True,
        help_text="Показывать этот товар в результатах поиска и каталогах.",
    )
    evotor_id = models.CharField(
        "ID Эвотор",
        max_length=128,
        blank=True,
        null=True,
    )
    article = AutoSlugField(
        "Артикул товара",
        max_length=64,
        populate_from="name",
        overwrite=False,
        editable=True,
        unique=True,
        help_text=(
            "Универсальный код товара (Артикул) является идентификатором для "
            "товара, который является специфичным для конкретного товара. "
            "Оставьте пустым, чтобы заполнить автоматически."
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
            "Выбирайте родительский товар только в том случае, если вы создаете дочерний "
            "товар. Например, если это размер "
            "4 конкретной футболки. Оставьте пустым, если это "
            "автономный товар (т.е. существует только одна версия"
            " этого товара)."
        ),
    )

    # name is mandatory for canonical products but optional for child products
    name = models.CharField("Название", max_length=255, blank=True)

    slug = SlugField("Ярлык", max_length=255, unique=True)
    description = models.TextField(
        "Описание",
        blank=True,
        help_text=("Описание которое отображается в списке товаров."),
    )
    short_description = models.CharField(
        "Краткое описание",
        max_length=255,
        null=True,
        blank=True,
        help_text=("Описание которое отображается в списке товаров."),
    )

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
        verbose_name="Тип товара",
        related_name="products",
        help_text="Выберите, что это за товар",
    )
    attributes = models.ManyToManyField(
        "catalogue.Attribute",
        through="ProductAttribute",
        verbose_name="Атрибуты",
        help_text=(
            "Атрибут товара — это то, что этот товар может"
            "иметь, например, размер, указанный его классом или в самом товаре"
        ),
    )
    #: It's possible to have options product class-wide, and per product.
    product_options = models.ManyToManyField(
        "catalogue.Option",
        blank=True,
        verbose_name="Опции товара",
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
        verbose_name="Дополнительные товары товара",
        help_text=("Дополнительные товары для данного товара"),
    )
    recommended_products = models.ManyToManyField(
        "catalogue.Product",
        through="ProductRecommendation",
        blank=True,
        verbose_name="Рекомендуемые товары",
        help_text=("Это товары, которые рекомендуется сопровождать основной товар."),
    )

    # Denormalised product rating - used by reviews app.
    # Product has no ratings if rating is None
    rating = models.FloatField("Рейтинг", null=True, editable=False)

    order = models.IntegerField(
        "Порядок",
        null=False,
        blank=False,
        default=0,
        help_text="Определяет порядок отображения в списке. (Чем меньше, тем выше в списке)",
    )
    cooking_time = models.IntegerField(
        "Время приготовления",
        null=False,
        blank=False,
        default=20,
        help_text="Приблизительное время, которое уйдет у повара на приготовление и сборку заказа на кухне. Указывается в минутах.",
    )
    weight = models.IntegerField(
        "Вес",
        null=True,
        blank=True,
        help_text="Вес товара в граммах.",
    )
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
            "Этот флаг указывает, можно ли использовать этот товар в предложении со скидками или нет"
        ),
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        app_label = "catalogue"
        ordering = ["-order"]
        permissions = (
            ("full_access", "Полный доступ к товарам"),
            ("read", "Просматривать товары и категории"),
            ("update_stockrecord", "Изменять наличие товаров"),
        )
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attr = ProductAttributesContainer(product=self)

    def __str__(self):
        return self.get_name()

    def get_absolute_url(self):
        """
        Return a product's variant absolute URL
        """
        product = self.parent if self.is_child else self
        category = product.categories.first()

        return reverse(
            "catalogue:detail",
            kwargs={
                "product_slug": product.slug,
                "category_slug": category.full_slug if category else "misc",
            },
        )

    def get_staff_url(self):
        """
        Return a category's absolute URL
        """
        return reverse("dashboard:catalogue-product", kwargs={"pk": self.id})

    def clean(self):
        """
        Validate a product. Those are the rules:

        +---------------+-------------+--------------+--------------+
        |               | stand alone | parent       | child        |
        +---------------+-------------+--------------+--------------+
        | name          | required    | required     | optional     |
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
        if not self.name:
            raise ValidationError("Ваш товар должен иметь название.")
        if not self.product_class:
            raise ValidationError("Ваш товар должен иметь класс товара.")
        if self.parent_id:
            raise ValidationError(
                "Родительский товар может иметь только дочерний товар."
            )

    def _clean_child(self):
        """
        Validates a child product
        """
        has_parent = self.parent or self.parent_id

        if not has_parent:
            raise ValidationError("Дочернему товару нужен родительский товар.")
        if has_parent and not self.parent.is_parent:
            raise ValidationError(
                "Вы можете назначать только дочерние товары родительским товарам."
            )
        if self.product_class:
            raise ValidationError("Дочерний товар не может иметь класс товара.")
        if self.pk and self.categories.exists():
            raise ValidationError("Дочернему товару не может быть присвоена категория.")
        # Note that we only forbid options on product level
        if self.pk and self.product_options.exists():
            raise ValidationError("У дочернего товара не может быть опций.")

    def _clean_parent(self):
        """
        Validates a parent product.
        """
        self._clean_standalone()
        if self.has_stockrecords:
            raise ValidationError("Родительский товар не может иметь складские записи.")

    def save(self, *args, **kwargs):
        # Генерация slug если он отсутствует
        if not self.slug:
            if self.is_child:
                name = self.name or self.get_variant_name()
                base_name = f"{self.parent.get_name()}-{name}" if self.name else name
                self.slug = slugify(base_name)
            else:
                self.slug = slugify(self.get_name())

        # Проверка уникальности slug
        if (
            not self.pk
            or self.__class__.objects.filter(slug=self.slug)
            .exclude(pk=self.pk)
            .exists()
        ):
            original_slug = self.slug
            counter = 1
            while (
                self.__class__.objects.filter(slug=self.slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        # Сохранение article и вызов родительского save()
        self.article = self.slug
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
            reason = "Указанный родительский товар является дочерним товаром."
        if self.has_stockrecords:
            reason = "Невозможно добавить дочерний товар к товару с учетными записями на складе."
        if not self.get_variant_attributes():
            reason = "Нет подходящих атрибутов для создания вариаций"

        is_valid = reason is None
        if give_reason:
            return is_valid, reason
        else:
            return is_valid

    @cached_property
    def options(self):
        """
        Returns a set of all valid options for this product.
        It's possible to have options product class-wide, and per product.
        """
        return self.get_class_options() | self.get_product_options()

    @cached_property
    def additionals(self):
        """
        Returns a set of all additionals for this product.
        """
        return self.get_class_additionals() | self.get_product_additionals()

    @cached_property
    def has_options(self):
        # Extracting annotated value with number of product class options
        # from product list queryset.
        # has_product_class_options = getattr(self, "has_product_class_options", None)
        # has_product_options = getattr(self, "has_product_options", None)
        # if has_product_class_options is not None and has_product_options is not None:
        #     return has_product_class_options or has_product_options

        return self.options.exists()

    @cached_property
    def has_additions(self):
        # Extracting annotated value with number of product class options
        # from product list queryset.
        # has_product_class_additionals = getattr(self, "has_product_class_additionals", None)
        # has_product_additionals = getattr(self, "has_product_additionals", None)
        # if has_product_class_additionals is not None and has_product_additionals is not None:
        #     return has_product_class_additionals or has_product_additionals
        return self.additionals.filter(is_public=True).exists()

    @cached_property
    def has_attributes(self):
        return self.attributes.exists()

    @cached_property
    def has_weight(self):
        return bool(self.weight)

    @cached_property
    def is_shipping_required(self):
        return self.get_product_class().requires_shipping

    @cached_property
    def has_stockrecords(self):
        """
        Test if this product has any stockrecords
        """
        return self.stockrecords.exists() if self.id else False

    @property
    def num_stockrecords(self):
        return self.stockrecords.count()

    @cached_property
    def attribute_summary(self):
        """
        Return a string of all of a product's attributes
        """
        attributes = self.get_attribute_values()
        return ", ".join([attribute.summary() for attribute in attributes])

    @cached_property
    def attributes_variants(self):
        """
        Return a string of all of a product's attributes
        """
        attributes = self.attribute_values.all()
        return ", ".join([attribute.summary() for attribute in attributes])

    def get_name(self):
        """
        Return a product's name or it's parent's name if it has no name
        """
        return self.name or (self.parent.name if self.parent_id else None)

    def get_variant_name(self):
        """
        Return a variant name
        """
        variants = "-".join(
            str(attr.option)
            for attr in self.attr.get_attribute_values().values_list(
                "option", flat=True
            )
        )
        return f"{self.get_name()}-{variants}" if variants else self.get_name()

    def get_variants(self):
        """
        Return a product's varian
        """
        if self.is_child:
            attributes = self.attribute_values.all()
            return ", ".join([attribute.summary() for attribute in attributes])

        return ""

    def get_variant_attributes(self):
        """
        Return a product's varian
        """
        attribute_values = self.attribute_values.filter(is_variant=True)
        return attribute_values

    get_name.short_description = "Название товара"

    def get_meta_title(self):
        return (
            self.meta_title
            or (self.parent.meta_title if self.is_child else None)
            or self.get_name()
        )

    get_meta_title.short_description = "Мета-заголовок товара"

    def get_meta_description(self):
        return (
            self.meta_description
            or (
                self.parent.meta_description
                if self.is_child and not self.meta_description
                else None
            )
            or striptags(self.short_description)
        )

    get_meta_description.short_description = "Мета-описание товара"

    def get_evotor_parent(self):
        return self.parent if self.parent else self.categories.first()

    def get_product_class(self):
        """
        Return a product's item class. Child products inherit their parent's.
        """
        if self.is_child:
            return self.parent.product_class
        else:
            return self.product_class

    get_product_class.short_description = "Класс товара"

    def get_class_options(self):
        return self.get_product_class().get_options()

    def get_product_options(self):
        if self.is_child:
            return self.parent.product_options.all()
        return self.product_options.all()

    def get_class_additionals(self):
        return self.get_product_class().class_additionals.filter(is_public=True)

    def get_product_additionals(self):
        if self.is_child:
            return self.parent.product_additionals.filter(is_public=True)
        return self.product_additionals.filter(is_public=True)

    # pylint: disable=no-member
    def get_categories(self):
        """
        Return a product's public categories or parent's if there is a parent product.
        """
        if self.is_child:
            return self.parent.categories.all()
        else:
            return self.categories.all()

    get_categories.short_description = "Категории"

    def get_evotor_parent_id(self):
        parent = self.get_evotor_parent()
        return parent.evotor_id if parent else ""

    def get_attribute_values(self):
        if not self.pk:
            return self.attribute_values.model.objects.none()

        attribute_values = self.attribute_values.all()
        if not self.is_child:
            return attribute_values

        return attribute_values.union(
            self.parent.attribute_values.exclude(
                attribute__code__in=attribute_values.values_list(
                    "attribute__code", flat=True
                )
            ),
            all=False,
        )

    # Images

    # pylint: disable=no-member
    def get_all_images(self):
        if self.is_child and not self.images.exists() and self.parent_id is not None:
            return self.parent.images.all()
        return self.images.all()
        # return self.images.all().order_by("display_order")

    def primary_image(self):
        """
        Returns the primary image for a product. Usually used when one can
        only display one product image, e.g. in a list of products.
        """
        images = self.get_all_images()
        # ordering = self.images.model.Meta.ordering
        # if not ordering or ordering[0] != "display_order":
        # Only apply order_by() if a custom model doesn't use default
        # ordering. Applying order_by() busts the prefetch cache of
        # the ProductManager
        # images = images.order_by("display_order")
        try:
            return images[0]
        except IndexError:
            # We return a dict with fields that mirror the key properties of
            # the ProductImage class so this missing image can be used
            # interchangeably in templates.  Strategy pattern ftw!
            return {"original": MissingImage(), "caption": self.name, "is_missing": True}

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
        result = self.reviews.aggregate(sum=Sum("score"), count=Count("id")).all()
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
    def num_helpful_reviews(self):
        return self.reviews.helpful().count()

    @cached_property
    def sorted_recommended_products(self):
        """Keeping order by recommendation ranking."""
        return [
            r.recommendation
            for r in self.primary_recommendations.select_related("recommendation").all()
        ]


class ProductRecommendation(models.Model):
    """
    'Through' model for product recommendations
    """

    primary = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="primary_recommendations",
        verbose_name="Основной товар",
    )
    recommendation = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        verbose_name="Рекомендуемый товар",
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
        app_label = "catalogue"
        ordering = ["primary", "-ranking"]
        unique_together = ("primary", "recommendation")
        verbose_name = "Рекомендация товара"
        verbose_name_plural = "Рекомендации товара"


class Attribute(models.Model):
    """
    Defines an attribute for a product class. (For example, number_of_pages for
    a 'book' class)
    """

    name = models.CharField("Имя", max_length=128)
    code = models.SlugField("Код", max_length=128, unique=True)

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
        (FILE, "Файл"),
        (IMAGE, "Изображение"),
        (OPTION, "Один атрибут из группы"),
        (MULTI_OPTION, "Множество атрибутов из группы"),
    )
    type = models.CharField(
        choices=TYPE_CHOICES,
        default=TYPE_CHOICES[0][0],
        max_length=20,
        verbose_name="Тип",
        help_text="Для создания атрибута вариации выберите «Множество атрибутов группы».",
    )
    option_group = models.ForeignKey(
        "catalogue.AttributeOptionGroup",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="product_attributes",
        verbose_name="Группа атрибутов",
        help_text="Выберите группу параметров, если используете тип «Атрибут группы» или «Множество атрибутов группы».",
    )
    required = models.BooleanField("Обязательный атрибут", default=False)

    objects = AttributeQuerySet.as_manager()

    class Meta:
        app_label = "catalogue"
        ordering = ["code"]
        verbose_name = "Атрибут"
        verbose_name_plural = "Атрибуты"

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
        if self.type == self.RICHTEXT and self.required:
            raise ValidationError(
                "Текстовое поле не должено быть обязательным атрибутом."
            )

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
            raise ValidationError("Должна быть строка")

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
        if isinstance(value, bool):
            raise ValidationError("Должно быть логическое значение ДА / НЕТ")

    def _validate_multi_option(self, value):
        try:
            values = iter(value)
        except TypeError:
            raise ValidationError("Должен быть списком или группой атрибутов.")
        # Validate each value as if it were an option
        # Pass in valid_values so that the DB isn't hit multiple times per iteration
        valid_values = self.option_group.options.values_list("option", flat=True)
        for value in values:
            self._validate_option(value, valid_values=valid_values)

    def _validate_option(self, value, valid_values=None):
        if not isinstance(value, get_model("catalogue", "AttributeOption")):
            raise ValidationError(
                "Должен быть экземпляром объекта модели AttributeOption."
            )
        if not value.pk:
            raise ValidationError("AttributeOption еще не сохранен.")
        if valid_values is None:
            valid_values = self.option_group.options.values_list("option", flat=True)
        if value.option not in valid_values:
            raise ValidationError(
                ("%(enum)s не корректен для %(attr)s") % {"enum": value, "attr": self}
            )

    def _validate_file(self, value):
        if value and not isinstance(value, File):
            raise ValidationError("Должно быть поле файла")

    _validate_image = _validate_file


class ProductAttribute(models.Model):
    """
    The "through" model for the m2m relationship between :py:class:`Product <.Product>` and
    :py:class:`ProductAttribute <.ProductAttribute>`  This specifies the value of the attribute for
    a particular product

    For example: ``number_of_pages = 295``
    """

    attribute = models.ForeignKey(
        "catalogue.Attribute",
        on_delete=models.CASCADE,
        verbose_name="Атрибут",
    )
    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="attribute_values",
        blank=True,
        null=True,
        verbose_name="товар",
    )
    product_class = models.ForeignKey(
        "catalogue.ProductClass",
        on_delete=models.CASCADE,
        related_name="attribute_values",
        blank=True,
        null=True,
        verbose_name="Класс товара",
    )

    is_variant = models.BooleanField("Используется для вариаций?", default=False)

    value_text = models.TextField("Текст", blank=True, null=True)
    value_integer = models.IntegerField(
        "Целое число", blank=True, null=True, db_index=True
    )
    value_boolean = models.BooleanField(
        "Логическое значение", blank=True, null=True, db_index=True
    )
    value_float = models.FloatField(
        "Дробное число", blank=True, null=True, db_index=True
    )
    value_richtext = models.TextField("Текстовое поле", blank=True, null=True)
    value_multi_option = models.ManyToManyField(
        "catalogue.AttributeOption",
        blank=True,
        related_name="multi_valued_attribute_values",
        verbose_name="Значения группы атрибутов",
    )
    value_option = models.ForeignKey(
        "catalogue.AttributeOption",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name="Одно значение из группы атрибутов",
    )
    value_file = models.FileField(
        upload_to=get_image_products_upload_path, max_length=255, blank=True, null=True
    )
    value_image = models.ImageField(
        upload_to=get_image_products_upload_path, max_length=255, blank=True, null=True
    )

    entity_content_type = models.ForeignKey(
        ContentType, blank=True, editable=False, on_delete=models.CASCADE, null=True
    )
    entity_object_id = models.PositiveIntegerField(
        null=True, blank=True, editable=False
    )
    _dirty = False

    def save(self, *args, **kwargs):
        if self.value_image:
            processor = ImageProcessor()
            optimized_image = processor.optimize_image(self.value_image)
            self.value_image.save(optimized_image.name, optimized_image, save=False)
        super().save(*args, **kwargs)

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
        app_label = "catalogue"
        unique_together = ("attribute", "product")
        verbose_name = "Значение атрибута товара"
        verbose_name_plural = "Значения атрибутов товара"

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
            return ("Значение атрибута товара", "Да")
        return ("Значение атрибута товара", "Нет")

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


class AttributeOptionGroup(models.Model):
    """
    Defines a group of options that collectively may be used as an
    attribute type

    For example, Language
    """

    name = models.CharField("Имя", max_length=128)
    evotor_id = models.CharField(
        "ID Эвотор",
        max_length=128,
        blank=True,
        null=True,
        unique=True,
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.evotor_id:
            self.evotor_id = str(uuid.uuid1())
        super().save(*args, **kwargs)

    class Meta:
        app_label = "catalogue"
        verbose_name = "Группа атрибутов"
        verbose_name_plural = "Группы атрибутов"

    @property
    def option_summary(self):
        options = [o.option for o in self.options.all()]
        return ", ".join(options)


class AttributeOption(models.Model):
    """
    Provides an option within an option group for an attribute type
    Examples: In a Language group, English, Greek, French
    """

    evotor_id = models.CharField(
        "ID Эвотор",
        max_length=128,
        blank=True,
        null=True,
        unique=True,
    )
    option = models.CharField("Опция", max_length=255)
    group = models.ForeignKey(
        "catalogue.AttributeOptionGroup",
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Группа",
    )

    def __str__(self):
        return self.option

    def save(self, *args, **kwargs):
        if not self.evotor_id:
            self.evotor_id = str(uuid.uuid1())
        super().save(*args, **kwargs)

    class Meta:
        app_label = "catalogue"
        unique_together = ("group", "option")
        verbose_name = "Параметр атрибута"
        verbose_name_plural = "Параметры атрибута"


class Option(models.Model):
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
        (MULTI_SELECT, "Несколько из списка"),
        (CHECKBOX, "Флажок"),
    )

    empty_label = "------"
    empty_radio_label = "Пропустить этот вариант"

    name = models.CharField("Имя", max_length=128, db_index=True)
    code = AutoSlugField("Код", max_length=128, unique=True, populate_from="name")
    type = models.CharField("Тип", max_length=255, default=TEXT, choices=TYPE_CHOICES)
    required = models.BooleanField("Обязательная ли эта опция?", default=False)
    option_group = models.ForeignKey(
        "catalogue.AttributeOptionGroup",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="product_options",
        verbose_name="Группа опций",
        help_text="Выберите группу параметров, если используете тип «Опция» или «Множество опций».",
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
        help_text="Управляет порядком опций товара на страницах сведений о товаре.",
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
                ("Группа опций не может использоваться с типом %s")
                % self.get_type_display()
            )
        return super().clean()

    class Meta:
        app_label = "catalogue"
        ordering = ["order", "name"]
        verbose_name = "Опция"
        verbose_name_plural = "Опиции"

    def __str__(self):
        return self.name


class ProductAdditional(models.Model):
    """
    'Through' model for product additional
    """

    primary_class = models.ForeignKey(
        "catalogue.ProductClass",
        on_delete=models.CASCADE,
        verbose_name="Основной класс",
        blank=True,
        null=True,
    )
    primary_product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        verbose_name="Основной товар",
        blank=True,
        null=True,
    )
    additional_product = models.ForeignKey(
        "catalogue.Additional",
        on_delete=models.CASCADE,
        verbose_name="Дополнительный товар",
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
        app_label = "catalogue"
        ordering = ["primary_product", "-ranking"]
        unique_together = ("primary_product", "additional_product")
        verbose_name = "Дополнительный товар"
        verbose_name_plural = "Дополнительные товары"


class Additional(models.Model):
    """
    An additional that can be selected for a particular item when the product
    is added to the basket.
    """

    name = models.CharField("Имя", max_length=128, db_index=True)
    article = AutoSlugField(
        "Артикул товара",
        max_length=64,
        populate_from="name",
        overwrite=False,
        editable=True,
        unique=True,
        help_text=(
            "Универсальный код товара (Артикул) является идентификатором для "
            "товара, который является специфичным для конкретного товара. "
            "Оставьте пустым, чтобы заполнить автоматически."
        ),
    )
    evotor_id = models.CharField(
        "ID Эвотор",
        max_length=128,
        blank=True,
        null=True,
    )
    order = models.IntegerField(
        "Порядок",
        null=True,
        blank=True,
        help_text="Управляет порядком опций товара на страницах сведений о товаре.",
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
    cost_price = models.DecimalField(
        "Цена закупки",
        decimal_places=2,
        max_digits=12,
        default=0,
        help_text="Закупочная цена за ед. доп товара",
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
    NO_VAT, VAT_10, VAT_18, VAT_0, VAT_18_118, VAT_10_110 = (
        "NO_VAT",
        "VAT_10",
        "VAT_18",
        "VAT_0",
        "VAT_18_118",
        "VAT_10_110",
    )
    VAT_CHOICES = (
        (NO_VAT, "Без НДС."),
        (VAT_0, "Основная ставка 0%"),
        (VAT_10, "Основная ставка 10%."),
        (VAT_10_110, "Расчётная ставка 10%."),
        (
            VAT_18,
            "Основная ставка 18%. С первого января 2019 года может указывать как на 18%, так и на 20% ставку.",
        ),
        (
            VAT_18_118,
            "Расчётная ставка 18%. С первого января 2019 года может указывать как на 18%, так и на 20% ставку.",
        ),
    )
    tax = models.CharField(
        "Налог в процентах", default=NO_VAT, choices=VAT_CHOICES, max_length=128
    )
    is_public = models.BooleanField(
        "Является общедоступным",
        default=True,
        db_index=True,
        help_text="Показывать этот дополнительный товар у товаров.",
    )
    stores = models.ManyToManyField(
        "store.Store",
        blank=True,
        verbose_name="Магазины",
    )
    image = models.ImageField(
        "Изображение",
        upload_to=get_image_additionals_upload_path,
        blank=True,
        null=True,
        max_length=255,
    )

    date_created = models.DateTimeField("Дата создания", auto_now_add=True)
    date_updated = models.DateTimeField("Дата изменения", auto_now=True, db_index=True)

    objects = AdditionalQuerySet.as_manager()

    parent_id = "201r02r2-5A02-403A-8tF6-r5C360350820"

    @cached_property
    def primary_image(self):
        """
        Returns the primary image for a product. Usually used when one can
        only display one product image, e.g. in a list of products.
        """
        if not self.image:
            mis_img = MissingImage()
            return {"original": mis_img, "caption": self.name, "is_missing": True}

        return {"original": self.image, "caption": self.name, "is_missing": False}

    class Meta:
        app_label = "catalogue"
        ordering = ["order", "name"]
        verbose_name = "Дополнительный товар"
        verbose_name_plural = "Дополнительные товары"

    def save(self, *args, **kwargs):
        if self.image:
            processor = ImageProcessor()
            optimized_image = processor.optimize_image(self.image)
            self.image.save(optimized_image.name, optimized_image, save=False)
        super().save(*args, **kwargs)

    def get_name(self):
        return self.name

    def get_evotor_parent_id(self):
        return self.parent_id

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    """
    An image of a product
    """

    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="товар",
    )
    code = NullCharField(
        "Код",
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )
    original = models.ImageField(
        "Оригинал", upload_to=get_image_products_upload_path, max_length=255
    )
    caption = models.CharField("Подпись", max_length=200, blank=True)

    #: Use display_order to determine which is the "primary" image
    display_order = models.PositiveIntegerField(
        "Порядок отображения",
        default=0,
        db_index=True,
        help_text=("Изображение с нулевым порядком отображения будет основным."),
    )
    date_created = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        app_label = "catalogue"
        # Any custom models should ensure that this ordering is unchanged, or
        # your query count will explode. See Product.primary_image.
        ordering = ["display_order"]
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товаров"

    def __str__(self):
        return "Image of '%s'" % self.product

    def is_primary(self):
        """
        Return bool if image display order is 0
        """
        return self.display_order == 0

    def save(self, *args, **kwargs):
        if self.original:
            processor = ImageProcessor()
            optimized_image = processor.optimize_image(self.original)
            self.original.save(optimized_image.name, optimized_image, save=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Always keep the display_order as consecutive integers. This avoids
        issue #855.
        """
        super().delete(*args, **kwargs)
        for idx, image in enumerate(self.product.images.all()):
            image.display_order = idx
            image.save()
