# pylint: disable=attribute-defined-outside-init
import datetime
import json
from django import http
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.authentication import SessionAuthentication

from django.conf import settings

from oscar.core.loading import get_model

from django import http
from django.views.generic import View


class AddShippingCharge(APIView):
    pass
