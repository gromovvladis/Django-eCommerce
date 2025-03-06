from django.urls import path
from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class CommunicationConfig(OscarConfig):
    label = "communication"
    namespace = "communication"
    name = "oscar.apps.communication"
    verbose_name = "Уведомления"

    def ready(self):
        from . import receivers

        self.webpush_save_view = get_class(
            "communication.webpush.views", "WebpushSaveSubscription"
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
