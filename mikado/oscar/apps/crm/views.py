import json
from django.conf import settings
from django.http import JsonResponse

from oscar.apps.crm.client import EvatorCloud
from oscar.apps.telegram.models import TelegramMessage
from oscar.core.loading import get_model
from oscar.apps.telegram.bot.synchron.send_message import send_message_to_staffs


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


import logging
logger = logging.getLogger("oscar.crm")

CRMEvent = get_model("crm", "CRMEvent")
Partner = get_model("partner", "Partner")

site_token = settings.EVOTOR_SITE_TOKEN
user_token = settings.EVOTOR_SITE_USER_TOKEN

site_login = settings.EVOTOR_SITE_LOGIN
site_pass = settings.EVOTOR_SITE_PASS


# ========= вспомогательные функции =========


def is_valid_site_token(request):
    # Проверка токена сайта
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response({"errors": [{"code": 1001}]}, status=status.HTTP_401_UNAUTHORIZED)
    
    auth_token = auth_header.split(" ")[1]
    if not auth_header or auth_token != site_token:
        return Response({"errors": [{"code": 1001}]}, status=status.HTTP_401_UNAUTHORIZED)
    
    return None  # Если все проверки прошли, возвращаем None

def is_valid_user_token(request):
    # Проверка токена сайта
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response({"errors": [{"code": 1001}]}, status=status.HTTP_401_UNAUTHORIZED)
    
    auth_token = auth_header.split(" ")[1]
    if not auth_header or auth_token != user_token:
        return Response({"errors": [{"code": 1001}]}, status=status.HTTP_401_UNAUTHORIZED)
    
    return None  # Если все проверки прошли, возвращаем None

def is_valid_user_login_and_pass(request):
    # Получение данных пользователя
    user_data = request.data
    login = user_data.get('login')
    password = user_data.get('password')

    if not login or not password or login != site_login or password != site_pass:
        return Response({"errors": [{"code": 1006}]}, status=status.HTTP_401_UNAUTHORIZED)

    return None  # Если все проверки прошли, возвращаем None

def is_valid_site_and_user_tokens(request):
    return is_valid_site_token(request) or is_valid_user_login_and_pass(request)



# ========= API Endpoints (Уведомления) =========

# сериализаторы
#  1. точка продажи и терминалы +
#  2. персонал +

#  3. продукт
#  3.1 категории и варианты продуктов (схемы и модификации)

#  4. заказ

# новые модели
#  1. чек 
#  2. документ 
#  3. событие +


# добавь испльзование курсора, если объектов много

class CRMPartnerEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/partners """

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs): 

        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }
        logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
        send_message_to_staffs(f"request: {json.dumps(request_info, ensure_ascii=False)}", TelegramMessage.TECHNICAL)

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed  
        
        partners_json = request.data.get('items')
        EvatorCloud().create_or_update_partners(partners_json)

        return JsonResponse({"status": "ok"}, status = 200) 


class CRMTerminalEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/terminals """

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs): 
        
        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }
        logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
        send_message_to_staffs(f"request: {json.dumps(request_info, ensure_ascii=False)}", TelegramMessage.TECHNICAL)

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed  
        
        terminals_json = request.data.get('items')
        EvatorCloud().create_or_update_terminals(terminals_json)

        return JsonResponse({"status": "ok"}, status = 200) 


class CRMStaffEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/staffs """

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs): 
        
        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }
        logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
        send_message_to_staffs(f"request: {json.dumps(request_info, ensure_ascii=False)}", TelegramMessage.TECHNICAL)

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed  
        
        staffs_json = request.data.get('items')
        EvatorCloud().create_or_update_staffs(staffs_json)

        return JsonResponse({"status": "ok"}, status = 200) 


class CRMRoleEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/roles """


    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs): 
        

        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }
        logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
        send_message_to_staffs(f"request: {json.dumps(request_info, ensure_ascii=False)}", TelegramMessage.TECHNICAL)

        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed  
        
        roles_json = request.data.get('items')
        EvatorCloud().create_or_update_site_roles(roles_json)

        return JsonResponse({"status": "ok"}, status = 200) 


class CRMDocsEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/docs """

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
                
        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }
        logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
        send_message_to_staffs(f"request: {json.dumps(request_info, ensure_ascii=False)}", TelegramMessage.TECHNICAL)
        
        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed
        
        CRMEvent.objects.create(
            body=f"Terminals recived {request.data}", 
            sender=CRMEvent.DOC,
            type=CRMEvent.INFO, 
        )
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMProductEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/products """

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
                
        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }
        logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
        send_message_to_staffs(f"request: {json.dumps(request_info, ensure_ascii=False)}", TelegramMessage.TECHNICAL)
        
        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed
        
        CRMEvent.objects.create(
            body=f"Terminals recived {request.data}", 
            sender=CRMEvent.PRODUCT,
            type=CRMEvent.INFO, 
        )
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMInstallationEndpointView(APIView):

    permission_classes = [AllowAny]

    """ https://mikado-sushi.ru/crm/api/subscription/setup """

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
                
        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }
        logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
        send_message_to_staffs(f"request: {json.dumps(request_info, ensure_ascii=False)}", TelegramMessage.TECHNICAL)
        
        not_allowed = is_valid_user_token(request)
        if not_allowed:
            return not_allowed
        
        CRMEvent.objects.create(
            body=f"Terminals recived {request.data}", 
            sender=CRMEvent.INSTALLATION,
            type=CRMEvent.INFO, 
        )
        return JsonResponse({"ok": "ok"}, status = 200)


# === login / register


class CRMLoginEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/user/login """
      
    authentication_classes = []
    permission_classes = [AllowAny]

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
    
    def post(self, request):
        
        request_info = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "data": request.data,
        }
        logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
        send_message_to_staffs(f"request: {json.dumps(request_info, ensure_ascii=False)}", TelegramMessage.TECHNICAL)

        not_allowed = is_valid_site_and_user_tokens(request)
        if not_allowed:
            return not_allowed

        return Response({"userId": request.data.get('userId'), "token": user_token}, status=status.HTTP_200_OK)
        


# мусор
# class CRMReceiptEndpointView(APIView):

#     permission_classes = [AllowAny]

#     """ https://mikado-sushi.ru/crm/api/receipts """

#     def put(self, request, *args, **kwargs):
#         return self.post(request, *args, **kwargs)
    
#     def post(self, request, *args, **kwargs): 

#         request_info = {
#             "method": request.method,
#             "path": request.path,
#             "headers": dict(request.headers),
#             "data": request.data,
#         }
#         logger.info(f"request: {json.dumps(request_info, ensure_ascii=False)}")
#         send_message_to_staffs(f"request: {json.dumps(request_info, ensure_ascii=False)}", TelegramMessage.TECHNICAL)

#         not_allowed = is_valid_user_token(request)
#         if not_allowed:
#             return not_allowed  
        
#         # receipts_json = request.data
#         # EvatorCloud().create_receipts(receipts_json)

#         return JsonResponse({"status": "ok"}, status = 200) 
