import json
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, Sum, fields
from django.http import JsonResponse

from oscar.apps.telegram.models import TelegramMessage
from oscar.core.loading import get_class, get_model
from oscar.apps.telegram.bot.synchron.send_message import send_message_to_staffs


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


import logging
logger = logging.getLogger("oscar.crm")

CRMEvent = get_model("crm", "CRMEvent")

site_token = settings.EVOTOR_SITE_TOKEN
user_token = settings.EVOTOR_SITE_USER_TOKEN

site_login = settings.EVOTOR_SITE_LOGIN
site_pass = settings.EVOTOR_SITE_PASS


# ========= API Endpoints (Уведомления) =========



def is_valid_site_token(request):
    # Проверка токена сайта
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != site_token:
        return Response({"errors": [{"code": 1001}]}, status=status.HTTP_401_UNAUTHORIZED)
    
    return None  # Если все проверки прошли, возвращаем None


def is_valid_user_token(request):
    # Получение данных пользователя
    user_data = request.data
    login = user_data.get('login')
    password = user_data.get('password')

    if not login or not password or login != site_login or password != site_pass:
        return Response({"errors": [{"code": 1006}]}, status=status.HTTP_401_UNAUTHORIZED)

    return None  # Если все проверки прошли, возвращаем None



def is_valid_site_and_user_tokens(request):
    return is_valid_site_token(request) or is_valid_user_token(request)


def test_function(request):
    request_info = {
        "method": request.method,
        "path": request.path,
        "headers": dict(request.headers),
        "data": request.data,
    }
    send_message_to_staffs(f"CRMStaffEndpointView post request: {json.dumps(request_info, ensure_ascii=False)}", TelegramMessage.TECHNICAL)
    


# ========= API Endpoints (Уведомления) =========

class CRMStaffEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/staffs """

    def post(self, request, *args, **kwargs):
        
        test_function(request)
        
        not_allowed = is_valid_site_token(request)
        if not_allowed:
            return not_allowed
        
        CRMEvent.objects.create(
            body=f"Staff recived {request.data}", 
            sender_choices=CRMEvent.STAFF,
            type=CRMEvent.INFO, 
        )
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMTerminalEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/terminals """

    def post(self, request, *args, **kwargs):
                
        test_function(request)
        
        not_allowed = is_valid_site_token(request)
        if not_allowed:
            return not_allowed
        
        CRMEvent.objects.create(
            body=f"Terminals recived {request.data}", 
            sender_choices=CRMEvent.TERMINAL,
            type=CRMEvent.INFO, 
        )
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMPartnerEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/partners """

    def post(self, request, *args, **kwargs):
                
        test_function(request)
        
        not_allowed = is_valid_site_token(request)
        if not_allowed:
            return not_allowed
        
        CRMEvent.objects.create(
            body=f"Terminals recived {request.data}", 
            sender_choices=CRMEvent.PARTNER,
            type=CRMEvent.INFO, 
        )
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMProductEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/products """

    def post(self, request, *args, **kwargs):
                
        test_function(request)
        
        not_allowed = is_valid_site_token(request)
        if not_allowed:
            return not_allowed
        
        CRMEvent.objects.create(
            body=f"Terminals recived {request.data}", 
            sender_choices=CRMEvent.PRODUCT,
            type=CRMEvent.INFO, 
        )
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMReceiptEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/receipts """

    def post(self, request, *args, **kwargs):
                
        test_function(request)
        
        not_allowed = is_valid_site_token(request)
        if not_allowed:
            return not_allowed
        
        CRMEvent.objects.create(
            body=f"Terminals recived {request.data}", 
            sender_choices=CRMEvent.RECEIPT,
            type=CRMEvent.INFO, 
        )
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMDocsEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/docs """

    def post(self, request, *args, **kwargs):
                
        test_function(request)
        
        not_allowed = is_valid_site_token(request)
        if not_allowed:
            return not_allowed
        
        CRMEvent.objects.create(
            body=f"Terminals recived {request.data}", 
            sender_choices=CRMEvent.DOC,
            type=CRMEvent.INFO, 
        )
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMInstallationEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/subscription/setup """

    def post(self, request, *args, **kwargs):
                
        test_function(request)
        
        not_allowed = is_valid_site_token(request)
        if not_allowed:
            return not_allowed
        
        CRMEvent.objects.create(
            body=f"Terminals recived {request.data}", 
            sender_choices=CRMEvent.INSTALLATION,
            type=CRMEvent.INFO, 
        )
        return JsonResponse({"ok": "ok"}, status = 200)



# === login / register


# class CRMRegisterEndpointView(APIView):
#     """ https://mikado-sushi.ru/crm/api/user/register """

#     authentication_classes = []
#     permission_classes = [AllowAny]

      
#     def post(self, request, *args, **kwargs):
#         send_message_to_staffs("CRMRegisterEndpointView POST", TelegramMessage.NEW)

#         content_type = request.headers.get('Content-Type', '')
#         logging.info(f"Received POST request with Content-Type: {content_type}")

#         request_info = {
#             "method": request.method,
#             "path": request.path,
#             "headers": dict(request.headers),
#             "query_params": request.query_params.dict(),
#         }
#         logging.info(f"CRMRegisterEndpointView post request: {json.dumps(request_info, ensure_ascii=False)}")
#         send_message_to_staffs(f"CRMRegisterEndpointView post request: {json.dumps(request_info, ensure_ascii=False)}", TelegramMessage.TECHNICAL)

#         return Response({"error": "Регистрация возможна только на ресурсе сайта. Свяжитесь с администрацией сайта"}, status=status.HTTP_409_CONFLICT)


class CRMLoginEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/user/login """
      
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        
        test_function(request)

        not_allowed = is_valid_site_and_user_tokens(request)
        if not_allowed:
            return not_allowed

        send_message_to_staffs(f"CRMLoginEndpointView post: login alowed", TelegramMessage.NEW)

        return Response({"userId": request.data.get('userId'), "token": user_token}, status=status.HTTP_200_OK)
        
