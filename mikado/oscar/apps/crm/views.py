from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, Sum, fields
from django.http import JsonResponse

from oscar.apps.crm.models import CRMToken
from oscar.apps.crm.serializers import CRMUserLoginSerializer, CRMUserRegisterSerializer
from oscar.apps.telegram.models import TelegramMessage
from oscar.core.loading import get_class, get_model
from oscar.apps.telegram.bot.synchron.send_message import send_message_to_staffs


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


import logging
logger = logging.getLogger("oscar.crm")

Partner = get_model("partner", "Partner")
Order = get_model("order", "Order")
Line = get_model("order", "Line")
CRMUser = get_model("crm", "CRMUser")


# ========= API Endpoints (Уведомления) =========

class CRMStaffEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/staffs """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMStaffEndpointView GET", TelegramMessage.NEW)
        logging.info(f"CRMStaffEndpointView get {request}")
        send_message_to_staffs(f"CRMStaffEndpointView get {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMProductEndpointView POST", TelegramMessage.NEW)
        logging.info(f"CRMStaffEndpointView post {request}")
        send_message_to_staffs(f"CRMStaffEndpointView post {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMTerminalEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/terminals """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMTerminalEndpointView GET", TelegramMessage.NEW)
        logging.info(f"CRMTerminalEndpointView get {request}")
        send_message_to_staffs(f"CRMTerminalEndpointView get {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMProductEndpointView POST", TelegramMessage.NEW)
        logging.info(f"CRMTerminalEndpointView post {request}")
        send_message_to_staffs(f"CRMTerminalEndpointView post {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMPartnerEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/partners """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMPartnerEndpointView GET", TelegramMessage.NEW)
        logging.info(f"CRMPartnerEndpointView get {request}")
        send_message_to_staffs(f"CRMPartnerEndpointView get {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMProductEndpointView POST", TelegramMessage.NEW)
        logging.info(f"CRMPartnerEndpointView post {request}")
        send_message_to_staffs(f"CRMPartnerEndpointView post {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMProductEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/products """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMProductEndpointView GET", TelegramMessage.NEW)
        logging.info(f"CRMProductEndpointView get {request}")
        send_message_to_staffs(f"CRMProductEndpointView get {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMProductEndpointView POST", TelegramMessage.NEW)
        logging.info(f"CRMProductEndpointView post {request}")
        send_message_to_staffs(f"CRMProductEndpointView post {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMReceiptEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/receipts """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMReceiptEndpointView EVENT", TelegramMessage.NEW)
        logging.info(f"CRMReceiptEndpointView get {request}")
        send_message_to_staffs(f"CRMReceiptEndpointView get {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMReceiptEndpointView POST", TelegramMessage.NEW)
        logging.info(f"CRMReceiptEndpointView post {request}")
        send_message_to_staffs(f"CRMReceiptEndpointView post {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMDocsEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/docs """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMDocsEndpointView GET", TelegramMessage.NEW)
        logging.info(f"CRMDocsEndpointView get {request}")
        send_message_to_staffs(f"CRMDocsEndpointView get {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMDocsEndpointView POST", TelegramMessage.NEW)
        logging.info(f"CRMDocsEndpointView post {request}")
        send_message_to_staffs(f"CRMDocsEndpointView post {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)


class CRMInstallationEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/subscription/setup """
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMInstallationEndpointView GET", TelegramMessage.NEW)
        logging.info(f"CRMInstallationEndpointView get {request}")
        send_message_to_staffs(f"CRMInstallationEndpointView get {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)
      

    def post(self, request, *args, **kwargs):
        send_message_to_staffs("CRMInstallationEndpointView POST", TelegramMessage.NEW)
        logging.info(f"CRMInstallationEndpointView post {request}")
        send_message_to_staffs(f"CRMInstallationEndpointView post {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)



# === login / register


class CRMRegisterEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/user/create """

    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMRegisterEndpointView GET", TelegramMessage.NEW)
        logging.info(f"CRMRegisterEndpointView get {request}")
        send_message_to_staffs(f"CRMRegisterEndpointView get {request}", TelegramMessage.TECHNICAL)
        return JsonResponse({"ok": "ok"}, status = 200)
      
    def post(self, request, *args, **kwargs):

        send_message_to_staffs("CRMRegisterEndpointView POST", TelegramMessage.NEW)
        logging.info(f"CRMRegisterEndpointView post {request}")
        send_message_to_staffs(f"CRMRegisterEndpointView post {request}", TelegramMessage.TECHNICAL)

        serializer = CRMUserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            logging.warning(f"CRMRegisterEndpointView invalid data: {serializer.errors}")
            send_message_to_staffs(f"CRMRegisterEndpointView invalid data: {serializer.errors}", TelegramMessage.TECHNICAL)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data['userId']
        custom_field = serializer.validated_data.get('customField', '')

        # Проверка заголовка Authorization
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            logging.warning(f"CRMRegisterEndpointView invalid authorization header: {auth_header}")
            send_message_to_staffs(f"CRMRegisterEndpointView invalid authorization header", TelegramMessage.TECHNICAL)
            return Response({'error': 'Invalid authorization header'}, status=status.HTTP_401_UNAUTHORIZED)

        token_value = auth_header.split(' ')[1]
        if token_value != settings.EVOTOR_TOKEN:
            logging.warning(f"CRMRegisterEndpointView unauthorized token: {token_value}")
            send_message_to_staffs(f"CRMRegisterEndpointView unauthorized token", TelegramMessage.TECHNICAL)
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

        # Проверка существования пользователя
        if CRMUser.objects.filter(user_id=user_id).exists():
            logging.warning(f"CRMRegisterEndpointView user already exists: {user_id}")
            send_message_to_staffs(f"CRMRegisterEndpointView user already exists: {user_id}", TelegramMessage.TECHNICAL)
            return Response({'error': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)

        # Создание нового пользователя и токена
        try:
            crm_user = CRMUser.objects.create(user_id=user_id, custom_field=custom_field)
            token = CRMToken.objects.create(crm_user=crm_user)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logging.error(f"CRMRegisterEndpointView error creating user: {e}")
            send_message_to_staffs(f"CRMRegisterEndpointView error creating user: {e}", TelegramMessage.TECHNICAL)
            return Response({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CRMLoginEndpointView(APIView):
    """ https://mikado-sushi.ru/crm/api/user/verify """
      
    authentication_classes = []
    permission_classes = []
    
    def get(self, request, *args, **kwargs):
        send_message_to_staffs("CRMLoginEndpointView GET", TelegramMessage.NEW)
        logging.info(f"CRMLoginEndpointView get {request}")
        send_message_to_staffs(f"CRMLoginEndpointView get {request}", TelegramMessage.NEW)
        return JsonResponse({"ok": "ok"}, status = 200)

    def post(self, request):

        send_message_to_staffs("CRMLoginEndpointView POST", TelegramMessage.NEW)
        logging.info(f"CRMLoginEndpointView get {request}")
        send_message_to_staffs(f"CRMLoginEndpointView get {request}", TelegramMessage.NEW)

        serializer = CRMUserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            logging.warning(f"CRMLoginEndpointView invalid data: {serializer.errors}")
            send_message_to_staffs(f"CRMLoginEndpointView invalid data: {serializer.errors}", TelegramMessage.NEW)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data['userId']

        logging.info(f"CRMLoginEndpointView post: user_id={user_id}")
        send_message_to_staffs(f"CRMLoginEndpointView post: user_id={user_id}", TelegramMessage.NEW)

        # Проверка заголовка Authorization
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            logging.warning(f"CRMLoginEndpointView invalid authorization header: {auth_header}")
            send_message_to_staffs(f"CRMLoginEndpointView invalid authorization header", TelegramMessage.NEW)
            return Response({'error': 'Invalid authorization header'}, status=status.HTTP_401_UNAUTHORIZED)

        token_value = auth_header.split(' ')[1]
        if token_value != settings.EVOTOR_TOKEN:
            logging.warning(f"CRMLoginEndpointView unauthorized token: {token_value}")
            send_message_to_staffs(f"CRMLoginEndpointView unauthorized token", TelegramMessage.NEW)
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

        # Поиск пользователя
        try:
            crm_user = CRMUser.objects.get(user_id=user_id)
        except CRMUser.DoesNotExist:
            logging.warning(f"CRMLoginEndpointView user not found: {user_id}")
            send_message_to_staffs(f"CRMLoginEndpointView user not found: {user_id}", TelegramMessage.NEW)
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Удаление старого токена, если он существует
        CRMToken.objects.filter(crm_user=crm_user).delete()

        # Создание нового токена
        try:
            token = CRMToken.objects.create(crm_user=crm_user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.error(f"CRMLoginEndpointView error creating token: {e}")
            send_message_to_staffs(f"CRMLoginEndpointView error creating token: {e}", TelegramMessage.NEW)
            return Response({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
