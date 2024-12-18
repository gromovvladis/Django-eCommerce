from django import http
from django.conf import settings
from django.utils.timezone import now
from django.views import generic
from django.db.models import Q

from oscar.core.loading import get_class, get_model
from oscar.core.utils import redirect_to_referrer
from oscar.views.generic import NotifEditMixin

PageTitleMixin = get_class("customer.mixins", "PageTitleMixin")
Notification = get_model("communication", "Notification")


class NotificationListView(PageTitleMixin, generic.ListView):
    model = Notification
    template_name = "oscar/communication/notifications/notifications_list.html"
    context_object_name = "notifications"
    paginate_by = settings.OSCAR_NOTIFICATIONS_PER_PAGE
    page_title = "Уведомления"
    active_tab = "notifications"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_type"] = self.list_type
        ctx["content_open"] = True
        ctx["summary"] = "Профиль"
        return ctx


class InboxView(NotificationListView):
    list_type = "inbox"

    def get_queryset(self):
        return self.model._default_manager.filter(
            recipient=self.request.user, location=self.model.INBOX
        )


class ArchiveView(NotificationListView):
    list_type = "archive"

    def get_queryset(self):
        return self.model._default_manager.filter(
            recipient=self.request.user, location=self.model.ARCHIVE
        )


class UpdateView(NotifEditMixin, generic.View):
    model = Notification
    http_method_names = ["post"]
    actions = ("archive", "delete")
    checkbox_object_name = "notification"

    def get_object(self, id):
        return self.model.objects.get(Q(recipient=self.request.user) & Q(id=id))

    def get_success_response(self):
        return redirect_to_referrer(self.request, "communication:notifications-inbox")

    def archive(self, request, notification):
        # for notification in notifications:
        notification.archive()

        num_unread = Notification.objects.filter(
            recipient=request.user, date_read=None, location="Inbox"
        ).count()

        if num_unread == 0:
            num_unread = ""

        return http.JsonResponse({"action": 'archive', "num_unread": num_unread, "status": 200}, status=200)

    def delete(self, request, notification):
        notification.delete()
        nums_total = Notification.objects.filter(
            recipient=request.user, location="Archive"
        ).count() 
        return http.JsonResponse({"action": 'delete', "nums_total": nums_total, "status": 200}, status=200)


class DetailView(PageTitleMixin, generic.DetailView):
    model = Notification
    template_name = "oscar/communication/notifications/notifications_detail.html"
    context_object_name = "notification"
    active_tab = "notifications"
    page_title = "Уведомление"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["content_open"] = True
        ctx["summary"] = "Профиль"
        return ctx

    def get_object(self, queryset=None):
        obj = super().get_object()
        if not obj.date_read:
            obj.date_read = now()
            obj.location = "Archive"
            obj.save()
        return obj

    def get_queryset(self):
        return self.model._default_manager.filter(recipient=self.request.user)
