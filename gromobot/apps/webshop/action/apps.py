from core.application import Config
from core.loading import get_class
from django.urls import path, re_path


class ActionConfig(Config):
    label = "action"
    name = "apps.webshop.action"
    verbose_name = "Акции-Баннеры и Промо-категории"

    namespace = "action"

    # pylint: disable=attribute-defined-outside-init, unused-import
    def ready(self):
        super().ready()
        self.actions_list_view = get_class("webshop.action.views", "ActionsListView")
        self.action_detail_view = get_class("webshop.action.views", "ActionDetailView")
        self.promocat_detail_view = get_class("webshop.action.views", "PromoCatDetailView")

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path("actions/", self.actions_list_view.as_view(), name="action-list"),
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
        ]
        return self.post_process_urls(urls)
