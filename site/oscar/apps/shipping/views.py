# pylint: disable=attribute-defined-outside-init
import datetime
import json

from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.authentication import SessionAuthentication

from django import http
from django.conf import settings
from django.views.generic import View

from oscar.core.loading import get_model


class AddShippingCharge(APIView):
    pass
