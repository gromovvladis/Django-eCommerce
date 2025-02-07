# -*- coding: utf-8 -*-
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils.translation import get_language, activate
from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")


"""
A basic example what a sitemap could look like for a multi-language Oscar
instance.
Creates entries for the homepage, for each product and each category.
Repeats those for each enabled language.
"""


class I18nSitemap(Sitemap):
    """
    A language-specific Sitemap class. Returns URLS for items for passed
    language.
    """

    def __init__(self, language="ru"):
        self.language = language
        self.original_language = get_language()

    def get_obj_location(self, obj):
        return obj.get_absolute_url()

    def location(self, obj):
        activate(self.language)
        location = self.get_obj_location(obj)
        activate(self.original_language)
        return location


class StaticSitemap(I18nSitemap):

    def items(self):
        return [
            "home",
        ]

    def get_obj_location(self, obj):
        return reverse(obj)


class ProductSitemap(I18nSitemap):

    def items(self):
        return Product.objects.browsable()


class CategorySitemap(I18nSitemap):

    def items(self):
        return Category.objects.filter(is_public=True)


neutral_sitemaps = {
    "static": StaticSitemap,
    "products": ProductSitemap,
    "categories": CategorySitemap,
}

# Construct the sitemaps for every language
base_sitemaps = {}
for name, sitemap_class in neutral_sitemaps.items():
    base_sitemaps[name] = sitemap_class()
