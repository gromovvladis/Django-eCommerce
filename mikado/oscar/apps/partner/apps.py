from oscar.core.application import OscarConfig
from django.urls import path
from oscar.core.loading import get_class


class PartnerConfig(OscarConfig):
    label = "partner"
    name = "oscar.apps.partner"
    verbose_name = "Точка продажи"

    namespace = "partner"

    # pylint: disable=unused-import
    def ready(self):
        from . import receivers

        self.partner_select = get_class("partner.views", "PartnerSelectModalView")

    def get_urls(self):
        urls = [
            path("api/select/", self.partner_select.as_view(), name="select"),
        ]

        return self.post_process_urls(urls)