from django.urls import path
from django.views.decorators.cache import cache_page

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class PageConfig(OscarConfig):
    label = "page"
    name = "oscar.apps.page"
    verbose_name = "Страницы сайта"

    namespace = "page"

    # pylint: disable=attribute-defined-outside-init, unused-import
    def ready(self):
        super().ready()

        self.homepage_view = get_class("page.views", "HomePageView")
        self.cookies_view = get_class("page.views", "GetCookiesView")
        self.service_worker_view = get_class("page.views", "service_worker")

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
