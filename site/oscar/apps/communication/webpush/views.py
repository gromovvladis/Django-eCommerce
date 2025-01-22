from django.conf import settings
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication

from oscar.core.loading import get_model

_dir = settings.STATIC_PRIVATE_ROOT

WebPushSubscription = get_model("communication", "WebPushSubscription")
    

def service_worker(request):
    return HttpResponse(open(_dir + '/js/dashboard/utils/service-worker.js', 'rb').read(), status=202, content_type='application/javascript')


class WebpushSaveSubscription(APIView):

    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        data = request.data
        subscription_info = data.get('subscription', {})
        endpoint = subscription_info.get('endpoint')
        keys = subscription_info.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        # Сохраняем подписку в базе данных
        subscription, created = WebPushSubscription.objects.get_or_create(
            endpoint=endpoint,
            defaults={
                'p256dh': p256dh,
                'auth': auth,
                'user': request.user if request.user.is_authenticated else None,
            },
        )

        return Response({'status': 'success', 'created': created})

