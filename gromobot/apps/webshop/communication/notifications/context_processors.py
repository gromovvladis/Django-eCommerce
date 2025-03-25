from core.loading import get_model

Notification = get_model("communication", "Notification")


def notifications(request):
    ctx = {}
    if getattr(request, "user", None) and request.user.is_authenticated:
        ctx["num_unread_notifications"] = ""
        num_unread = Notification.objects.filter(
            recipient=request.user, date_read=None, location="Inbox"
        ).count()
        if num_unread > 0:
            ctx["num_unread_notifications"] = num_unread
    return ctx
