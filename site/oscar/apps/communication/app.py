from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views import generic

from oscar.core.application import Application
from oscar.core.loading import get_class


class CommunicationApplication(Application):
    name = "communication"

    notification_inbox_view = get_class(
        "communication.notifications.views", "InboxView"
    )
    notification_archive_view = get_class(
        "communication.notifications.views", "ArchiveView"
    )
    notification_update_view = get_class(
        "communication.notifications.views", "UpdateView"
    )
    notification_detail_view = get_class(
        "communication.notifications.views", "DetailView"
    )

    def get_urls(self):
        urls = [
            # Notifications
            # Redirect to notification inbox
            path(
                "notifications/",
                generic.RedirectView.as_view(
                    url="/accounts/notifications/inbox/", permanent=False
                ),
            ),
            path(
                "notifications/inbox/",
                login_required(self.notification_inbox_view.as_view()),
                name="notifications-inbox",
            ),
            path(
                "notifications/archive/",
                login_required(self.notification_archive_view.as_view()),
                name="notifications-archive",
            ),
            path(
                "notifications/update/",
                login_required(self.notification_update_view.as_view()),
                name="notifications-update",
            ),
            path(
                "notifications/<int:pk>/",
                login_required(self.notification_detail_view.as_view()),
                name="notifications-detail",
            ),
        ]

        return self.post_process_urls(urls)


application = CommunicationApplication()
