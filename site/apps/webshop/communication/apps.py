from django.urls import path
from core.application import Config
from core.loading import get_class


class CommunicationConfig(Config):
    label = "communication"
    namespace = "communication"
    name = "apps.webshop.communication"
    verbose_name = "Уведомления"

    def ready(self):
        from . import receivers

        self.webpush_save_view = get_class(
            "webshop.communication.webpush.views", "WebpushSaveSubscription"
        )

    def get_urls(self):
        urls = [
            path(
                "webpush/save-subscription/",
                self.webpush_save_view.as_view(),
                name="webpush-save",
            ),
        ]

        return self.post_process_urls(urls)
