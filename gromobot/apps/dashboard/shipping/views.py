# pylint: disable=attribute-defined-outside-init
import json

from core.loading import get_class, get_model
from django import http
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, UpdateView, View
from django_tables2 import SingleTableView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

ShippingZonaForm = get_class("dashboard.shipping.forms", "ShippingZonaForm")
ShippingZonesTable = get_class("dashboard.shipping.tables", "ShippingZonesTable")

ShippingZona = get_model("shipping", "ShippingZona")

_dir = settings.STATIC_PRIVATE_ROOT

# ====== zones =================================


class ShippingZonesGeoJsonView(APIView):
    """
    Return the 'shipping all zones json'.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        json_file = json.loads(
            open(
                _dir + "/js/dashboard/shipping/geojson/shipping_zones.geojson", "rb"
            ).read()
        )
        return http.JsonResponse(json_file, status=200)


class ShippingZonaView(APIView):
    """
    Return the 'shipping zona params' Only Dashboard.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]
    model = ShippingZona

    def post(self, request, *args, **kwargs):
        try:
            zona_id = request.POST.get("zona_id")
            zona = self.model.objects.get(id=zona_id)
            res = {
                "number": zona.id,
                "name": zona.name,
                "order_price": zona.order_price,
                "shipping_price": zona.shipping_price,
                "isAvailable": zona.isAvailable,
                "isHide": zona.isHide,
            }
            return http.JsonResponse(res, status=200)
        except Exception:
            return http.JsonResponse({"error": "Зона доставки не найдена"}, status=200)


class ShippingZonesView(SingleTableView):
    """
    An overview view which displays several reports about the shop.

    Supports the permission-based dashboard. It is recommended to add a
    :file:`dashboard/index_nonstaff.html` template because Oscar's
    default template will display potentially sensitive store information.
    """

    model = ShippingZona
    table_class = ShippingZonesTable
    context_table_name = "zones"
    template_name = "dashboard/shipping/shipping_zones.html"
    paginate_by = settings.DASHBOARD_ITEMS_PER_PAGE

    # def dispatch(self, request, *args, **kwargs):
    #     return super().dispatch(request, *args, **kwargs)

    # def get(self, request, *args, **kwargs):
    #     return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Build the queryset for this list.
        """

        return self.model.objects.all()


class ShippingZonesCreateView(CreateView):
    template_name = "dashboard/shipping/shipping_form.html"
    model = ShippingZona
    form_class = ShippingZonaForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Добавить новую зону доставки"
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Зона доставки успешно создана.")
        return reverse("dashboard:shipping-zones")


class ShippingZonesUpdateView(UpdateView):
    template_name = "dashboard/shipping/shipping_form.html"
    model = ShippingZona
    form_class = ShippingZonaForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["number"] = self.object.id
        ctx["title"] = "Обновить зону доставки №%s" % self.object.id
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Зона доставки успешно обновлена.")
        return reverse("dashboard:shipping-zones")


class ShippingZonesDeleteView(DeleteView):
    template_name = "dashboard/shipping/shipping_zona_delete.html"
    model = ShippingZona

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Удалить зону доставки '%s'" % self.object.id
        ctx["number"] = self.object.id
        ctx["description"] = self.object.description
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Зона доставки успешно удалена.")
        return reverse("dashboard:shipping-zones")


class ShippingZonesHideView(UpdateView):
    model = ShippingZona

    def post(self, request, *args, **kwargs):
        try:
            zona_id = kwargs.get("pk")
            zona = self.model.objects.get(id=zona_id)
            zona.isHide = not zona.isHide
            zona.save()
            return self.get_success_url()
        except Exception:
            return self.get_error_url()

    def get_success_url(self):
        messages.info(self.request, "Зона доставки успешно обновлена.")
        return redirect("dashboard:shipping-zones")

    def get_error_url(self):
        messages.error(self.request, "Зона доставки не была обновлена.")
        return redirect("dashboard:shipping-zones")


class ShippingZonesAvailableView(View):
    model = ShippingZona

    def post(self, request, *args, **kwargs):
        try:
            zona_id = kwargs.get("pk")
            zona = self.model.objects.get(id=zona_id)
            zona.isAvailable = not zona.isAvailable
            zona.save()
            return self.get_success_url()
        except Exception:
            return self.get_error_url()

    def get_success_url(self):
        messages.info(self.request, "Зона доставки успешно обновлена.")
        return redirect("dashboard:shipping-zones")

    def get_error_url(self):
        messages.error(self.request, "Зона доставки не была обновлена.")
        return redirect("dashboard:shipping-zones")


# ====== zones =================================


class ShippingActiveView(View):
    pass


class ShippingListView(View):
    pass


# ====== zones =================================


class ShippingStatsView(View):
    pass


class ShippingStoreView(View):
    pass


class ShippingCouriersView(View):
    pass


class ShippingCouriersListView(View):
    pass


class ShippingCouriersDetailView(View):
    pass
