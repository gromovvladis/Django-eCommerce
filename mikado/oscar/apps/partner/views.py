# pylint: disable=attribute-defined-outside-init
from django import http
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

User = get_user_model()


Partner = get_model("partner", "Partner")
PartnerSelectForm = get_class("partner.forms", "PartnerSelectForm")


class PartnerSelectModalView(APIView):
    """
    Resiter via sms.
    """
    permission_classes = [AllowAny]

    template_name = "oscar/partner/partner_modal.html"
    form_class = PartnerSelectForm
    redirect_field_name = "next"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        partner_select = render_to_string(self.template_name, context, request=request)
        return http.JsonResponse({
             "partner_modal": partner_select,
             "partner_default": 1,
        }, status = 202)


    def get_context_data(self, *args, **kwargs):
        return {
            "partner_form": self.get_partner_form()
        }

    def post(self, request, *args, **kwargs):
        form = self.get_partner_form()
        if form.is_valid():
            partner_id = form.clean_data["partner_id"]
            request.basket.partner_id = partner_id
            response = http.JsonResponse({"success": "Точка продажи выбрана", "status": 200}, status=200)
            response.set_cookie('partner', partner_id)
            return response

        return http.JsonResponse({"error": "Код не верный", "status": 400}, status=404)


    def get_partner_form(self):
        return self.form_class(**self.get_form_class_kwargs())


    def get_form_class_kwargs(self):
        kwargs = {}
        kwargs["initial"] = {
            "partner_id": self.request.POST.get("partner_id"),
        }
        return kwargs