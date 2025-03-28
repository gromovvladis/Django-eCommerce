from core.application import Config
from core.loading import get_class
from django.apps import apps
from django.urls import include, re_path


class CatalogueOnlyConfig(Config):
    label = "catalogue"
    name = "apps.webshop.catalogue"
    verbose_name = "Каталог"

    namespace = "catalogue"

    # pylint: disable=attribute-defined-outside-init, unused-import
    def ready(self):
        from . import receivers

        super().ready()

        self.detail_view = get_class("webshop.catalogue.views", "ProductDetailView")
        self.category_view = get_class("webshop.catalogue.views", "ProductCategoryView")
        self.range_view = get_class("webshop.offer.views", "RangeDetailView")

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            re_path(
                r"^(?P<category_slug>[\w-]+(/[\w-]+)*)/(?P<product_slug>[\w-]+)$",
                self.detail_view.as_view(),
                name="detail",
            ),
            re_path(
                r"^(?P<category_slug>[\w-]+(/[\w-]+)*)/$",
                self.category_view.as_view(),
                name="category",
            ),
            re_path(
                r"^ranges/(?P<slug>[\w-]+)/$", self.range_view.as_view(), name="range"
            ),
        ]
        return self.post_process_urls(urls)


class CatalogueReviewsOnlyConfig(Config):
    label = "catalogue"
    name = "apps.webshop.catalogue.reviews"
    verbose_name = "Отзывы на товары"

    # pylint: disable=attribute-defined-outside-init, unused-import
    def ready(self):
        from . import receivers

        super().ready()

        self.reviews_app = apps.get_app_config("product_reviews")

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            re_path(
                r"^(?P<product_slug>[\w-]*)_(?P<product_pk>\d+)/reviews/",
                include(self.reviews_app.urls[0]),
            ),
        ]
        return self.post_process_urls(urls)


class CatalogueConfig(CatalogueOnlyConfig, CatalogueReviewsOnlyConfig):
    """
    Composite class combining Products with Reviews
    """
