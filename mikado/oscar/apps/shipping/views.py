# pylint: disable=attribute-defined-outside-init
import datetime
import json
from django import http
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from django.conf import settings


class DelievryTimeView(APIView):

    permission_classes = [AllowAny]
 
    def post(self, request, *args, **kwargs):
        yandex_time = request.POST.get('yandex_time')
        minutes = round(float(yandex_time) / 60) + 60
        return Response({
            "delivery_time": minutes,
            "status": 200,
            }, status=200)


class PickUpTimeView(APIView):

    permission_classes = [AllowAny]
 
    def post(self, request, *args, **kwargs):
        minutes =  60
        return Response({
            "pickup_time": minutes,
            "status": 200,
            }, status=200)


class DeliveryLaterView(APIView):
    """
    Время доставки к определенному времени
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):

        time_now = datetime.datetime.today()
        hours_delta = 2

        if time_now.minute > 30:
            hours_delta = 3

        data = {
            'minHours': 10,
            'maxHours': 22,
            'minDate': format(time_now.replace(minute=0) + datetime.timedelta(hours=hours_delta),'%Y-%m-%dT%H:%M'),
            'maxDate': format(time_now.replace(minute=59, hour=22) + datetime.timedelta(days=14),'%Y-%m-%dT%H:%M')
        }
        return http.JsonResponse({"datapicker": data}, status = 200)
    
   
class DeliveryZonesView(APIView):
    """
    Return the 'delivery zones'.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        dir = settings.STATIC_PRIVATE_ROOT
        filename = 'delivery_zones.geojson'
        json_file = json.loads(open(dir + '/js/delivery/geojson/' + filename, 'rb').read())
        return http.JsonResponse(json_file, status=202)
