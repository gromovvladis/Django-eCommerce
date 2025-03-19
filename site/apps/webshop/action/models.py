from functools import cached_property

from django.db import models
from django.template.defaultfilters import striptags
from django.urls import reverse
from core.models.img.missing_image import MissingImage
from core.utils import slugify
from core.models.fields import AutoSlugField
from core.models.img.image_processor import ImageProcessor
from core.models.img.paths import (
    get_image_actions_upload_path,
    get_image_promocategory_upload_path,
)


class Action(models.Model):
    slug = AutoSlugField("Ярлык", max_length=128, unique=True, populate_from="title")
    image = models.ImageField(
        blank=False, upload_to=get_image_actions_upload_path, null=False
    )
    title = models.CharField("Заголовок", max_length=128, blank=False, null=False)
    description = models.TextField("Описание", blank=True)
    order = models.IntegerField("Порядок", null=False, blank=False, default=0)
    is_active = models.BooleanField(default=True)
    products = models.ManyToManyField(
        "catalogue.Product",
        blank=True,
        help_text=("Товары которые будут показаны на странице акции."),
        verbose_name="Связаные товары",
        related_name="actions",
        through="action.ActionProduct",
    )

    date_created = models.DateTimeField("Дата создания", auto_now_add=True)
    date_updated = models.DateTimeField("Дата изменения", auto_now=True)

    meta_title = models.CharField(
        "Мета заголовок", max_length=255, blank=True, null=True
    )
    meta_description = models.TextField("Мета описание", blank=True, null=True)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Акция-баннер"
        verbose_name_plural = "Акции-баннеры"

    def __str__(self):
        return self.title or self.slug

    def get_title(self):
        return self.title

    def get_meta_title(self):
        return self.meta_title or self.get_title()

    def get_meta_description(self):
        return self.meta_description or striptags(self.description)

    get_meta_description.short_description = "Мета-описание акции"

    @cached_property
    def full_slug(self):
        return self.slug

    def generate_slug(self):
        return slugify(self.title)

    def save(self, *args, **kwargs):
        if self.image:
            processor = ImageProcessor()
            optimized_image = processor.optimize_image(self.image)
            self.image.save(optimized_image.name, optimized_image, save=False)

        if not self.slug:
            self.slug = self.generate_slug()
        super().save(*args, **kwargs)

    @cached_property
    def has_image(self):
        if self.image:
            return True
        return False

    @cached_property
    def primary_image(self):
        """
        Returns the primary image for a product. Usually used when one can
        only display one product image, e.g. in a list of products.
        """
        img = self.image
        caption = self.title
        if not img:
            mis_img = MissingImage()
            return {"original": mis_img, "caption": caption, "is_missing": True}

        return {"original": img, "caption": caption, "is_missing": False}

    def get_absolute_url(self):
        return reverse("action:action-detail", kwargs={"action_slug": self.full_slug})

    @cached_property
    def has_products(self):
        return self.products.exists()

    @property
    def all_products(self):
        """
        Return a queryset of products in this action
        """
        return (
            self.products.select_related("parent", "product_class")
            .prefetch_related(
                "stockrecords", "images", "parent__product_class", "categories"
            )
            .all()
        )


class ActionProduct(models.Model):
    """
    Allow ordering products inside ranges
    Exists to allow customising.
    """

    action = models.ForeignKey("action.Action", on_delete=models.CASCADE)
    product = models.ForeignKey("catalogue.Product", on_delete=models.CASCADE)
    display_order = models.IntegerField(default=0)

    class Meta:
        app_label = "action"
        unique_together = ("action", "product")


class PromoCategory(models.Model):
    slug = AutoSlugField("Ярлык", max_length=128, unique=True, populate_from="title")
    image = models.ImageField(blank=True, upload_to=get_image_promocategory_upload_path)
    title = models.CharField("Заголовок", max_length=128, blank=False, null=False)
    description = models.TextField("Описание", blank=True)
    order = models.IntegerField("Порядок", null=False, blank=False, default=0)
    is_active = models.BooleanField(default=True)
    products = models.ManyToManyField(
        "catalogue.Product",
        blank=True,
        verbose_name="Связаные товары",
        help_text=("Товары которые будут показаны в продвигаемой категории."),
        related_name="promo_categories",
        through="action.PromoCategoryProduct",
    )

    date_created = models.DateTimeField("Дата создания", auto_now_add=True)
    date_updated = models.DateTimeField("Дата изменения", auto_now=True)

    meta_title = models.CharField(
        "Мета заголовок", max_length=255, blank=True, null=True
    )
    meta_description = models.TextField("Мета описание", blank=True, null=True)

    PROMO, RECOMENDATION, ACTION = "PROMO", "RECOMEND", "ACTION"
    choices = (
        (PROMO, "Промо-категория"),
        (RECOMENDATION, "Рекомендованные товары"),
        (ACTION, "Акция на товары"),
    )
    type = models.CharField(
        max_length=255,
        choices=choices,
        verbose_name="Тип категории",
        default=RECOMENDATION,
    )

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Промо-товар"
        verbose_name_plural = "Промо-товары"

    def __str__(self):
        return self.title or self.slug

    def get_title(self):
        return self.title

    def get_meta_title(self):
        return self.meta_title or self.get_title()

    def get_meta_description(self):
        return self.meta_description or striptags(self.description)

    get_meta_description.short_description = "Мета-описание промо-категории"

    @property
    def full_slug(self):
        return self.slug

    def generate_slug(self):
        return slugify(self.title)

    def save(self, *args, **kwargs):
        if self.image:
            processor = ImageProcessor()
            optimized_image = processor.optimize_image(self.image)
            self.image.save(optimized_image.name, optimized_image, save=False)

        if not self.slug:
            self.slug = self.generate_slug()
        super().save(*args, **kwargs)

    @cached_property
    def has_image(self):
        if self.image:
            return True
        return False

    @cached_property
    def primary_image(self):
        img = self.image
        caption = self.title
        if not img:
            mis_img = MissingImage()
            return {"original": mis_img, "caption": caption, "is_missing": True}

        return {"original": img, "caption": caption, "is_missing": False}

    @cached_property
    def has_products(self):
        return self.products.exists()

    @property
    def all_products(self):
        """
        Return a queryset of products in this action
        """
        return (
            self.products.select_related("parent", "product_class")
            .prefetch_related(
                "stockrecords", "images", "parent__product_class", "categories"
            )
            .all()
        )

    def get_absolute_url(self):
        return reverse("action:promo-detail", kwargs={"action_slug": self.full_slug})


class PromoCategoryProduct(models.Model):
    """
    Allow ordering products inside ranges
    Exists to allow customising.
    """

    promo_category = models.ForeignKey("action.PromoCategory", on_delete=models.CASCADE)
    product = models.ForeignKey("catalogue.Product", on_delete=models.CASCADE)
    display_order = models.IntegerField(default=0)

    class Meta:
        app_label = "action"
        unique_together = ("promo_category", "product")
