from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


from webpush.models import SubscriptionInfo, PushInformation


class WebpushSaveSubscription(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        try:
            data = request.data
            subscription_info = data.get("subscription", {})
            endpoint = subscription_info.get("endpoint")
            keys = subscription_info.get("keys", {})
            p256dh = keys.get("p256dh")
            auth = keys.get("auth")
            group = data.get("group", "staff")
            subscription, created = SubscriptionInfo.objects.get_or_create(
                endpoint=endpoint,
                defaults={
                    "p256dh": p256dh,
                    "auth": auth,
                },
            )
            if request.user.is_authenticated:
                PushInformation.objects.get_or_create(
                    user=request.user,
                    subscription=subscription,
                    defaults={"group": group},
                )
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        return Response({"status": "success", "created": created})
