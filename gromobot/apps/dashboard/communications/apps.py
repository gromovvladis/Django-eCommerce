from core.application import DashboardConfig
from core.loading import get_class
from django.urls import path, re_path


class CommunicationsDashboardConfig(DashboardConfig):
    label = "communications_dashboard"
    name = "apps.dashboard.communications"
    verbose_name = "Панель управления - Сообщения"

    default_permissions = ("user.full_access",)

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.email_list_view = get_class(
            "dashboard.communications.views", "EmailListView"
        )
        self.sms_list_view = get_class("dashboard.communications.views", "SmsListView")
        self.sended_sms_view = get_class(
            "dashboard.communications.views", "SendedSmsView"
        )
        self.update_view = get_class("dashboard.communications.views", "UpdateView")

    def get_urls(self):
        urls = [
            path("email/", self.email_list_view.as_view(), name="email-list"),
            path("sms/", self.sms_list_view.as_view(), name="sms-list"),
            path("sended-sms/", self.sended_sms_view.as_view(), name="sended-sms"),
            re_path(
                r"^(?P<slug>[\w-]+)/$", self.update_view.as_view(), name="comms-update"
            ),
        ]
        return self.post_process_urls(urls)
