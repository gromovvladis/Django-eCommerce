from core.application import Config
from core.loading import get_class
from django.urls import path
from django.views.decorators.cache import cache_page


class PageConfig(Config):
    label = "page"
    name = "apps.webshop.page"
    verbose_name = "Страницы сайта"

    namespace = "page"

    # pylint: disable=attribute-defined-outside-init, unused-import
    def ready(self):
        super().ready()

        self.homepage_view = get_class("webshop.page.views", "HomePageView")
        self.cookies_view = get_class("webshop.page.views", "GetCookiesView")
        self.service_worker_view = get_class("webshop.page.views", "service_worker")

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path("", self.homepage_view.as_view(), name="homepage"),
            path(
                "api/cookies/",
                cache_page(50000)(self.cookies_view.as_view()),
                name="cookies",
            ),
            path("service-worker.js", self.service_worker_view),
        ]
        return self.post_process_urls(urls)
