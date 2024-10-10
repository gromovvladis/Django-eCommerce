from decimal import Decimal as D

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, Sum, fields
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView, UpdateView, DeleteView, CreateView, View

from oscar.apps.telegram.models import TelegramMessage
from oscar.core.loading import get_class, get_model
from oscar.apps.telegram.bot.synchron.send_message import send_message_to_staffs

from django.http import JsonResponse
from rest_framework.views import APIView
from crm.client import EvotorAPIClient

import logging
logger = logging.getLogger("oscar.dashboard")

Partner = get_model("partner", "Partner")
Order = get_model("order", "Order")
Line = get_model("order", "Line")


# ========= API Endpoints (Уведомления) =========

class CRMStaffEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/staffs """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMStaffEndpointView get", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMStaffEndpointView post", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMTerminalEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/terminals """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMTerminalEndpointView get", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMTerminalEndpointView post", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMPartnerEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/partners """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMPartnerEndpointView get", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMPartnerEndpointView post", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMProductEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/products """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMProductEndpointView get", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMProductEndpointView post", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMReceiptEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/receipts """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMReceiptEndpointView get", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMReceiptEndpointView post", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMDocsEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/docs """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMDocsEndpointView get", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMDocsEndpointView post", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMSubscriptionSetupEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/subscription/setup """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMSubscriptionSetupEndpointView get", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMSubscriptionSetupEndpointView post", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMSubscriptionEventEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/subscription/event """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMSubscriptionEventEndpointView get", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMSubscriptionEventEndpointView post", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMTokenEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/user/token """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMTokenEndpointView get", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMTokenEndpointView post", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMUserCreateEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/user/create """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMUserCreateEndpointView get", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMUserCreateEndpointView post", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMUserVerifyEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/user/verify """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMUserVerifyEndpointView get", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMUserVerifyEndpointView post", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)


# ========= Dashboard views =========


class CRMOrderListView(ListView):
    pass


class CRMPartnerListView(ListView):
    pass


class CRMStaffListView(ListView):
    pass


class CRMProductListView(ListView):
    pass


class CRMReceiptListView(ListView):
    pass


class CRMDocListView(ListView):
    pass
