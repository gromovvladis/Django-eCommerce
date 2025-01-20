from django.urls import path, re_path
from oscar.core.application import OscarConfig
from oscar.core.loading import get_class

from django.views.decorators.cache import cache_page

class HomeConfig(OscarConfig):
    label = "home"
    name = "oscar.apps.home"
    verbose_name = "Домашнаяя страница"

    namespace = "home"

    # pylint: disable=attribute-defined-outside-init, unused-import
    def ready(self):
        super().ready()

        self.home_view = get_class("home.views", "HomeView")
        self.actions_view = get_class("home.views", "ActionsView")
        self.action_detail_view = get_class("home.views", "ActionDetailView")
        self.promocat_detail_view = get_class("home.views", "PromoCatDetailView")
        self.cookies_view = get_class("home.views", "GetCookiesView")
        
        self.webpush_save_view = get_class("home.views", "WebpushSaveSubscription")
        self.service_worker_view = get_class("home.views", "service_worker")

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path("", self.home_view.as_view(), name="index"),

            path("webpush/save-subscription/", self.webpush_save_view.as_view(), name="webpush-save"),
            path('service-worker.js', self.service_worker_view, name='service_worker'),

            path("actions/", self.actions_view.as_view(), name="actions"),
            re_path(
                r"^actions/(?P<action_slug>[\w-]+(/[\w-]+)*)/$",
                self.action_detail_view.as_view(),
                name="action-detail",
            ),
            re_path(
                r"^promo/(?P<action_slug>[\w-]+(/[\w-]+)*)/$",
                self.promocat_detail_view.as_view(),
                name="promo-detail",
            ),
            path("api/cookies/", cache_page(60 * 60 * 12)(self.cookies_view.as_view()), name="cookies"),
        ]
        return self.post_process_urls(urls)
