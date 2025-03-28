from core.loading import get_model
from django.contrib import admin

Email = get_model("communication", "Email")
Notification = get_model("communication", "Notification")
CommunicationEventType = get_model("communication", "CommunicationEventType")

admin.site.register(Email)
admin.site.register(Notification)
admin.site.register(CommunicationEventType)
