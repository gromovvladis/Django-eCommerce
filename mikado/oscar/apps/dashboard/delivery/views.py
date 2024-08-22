# pylint: disable=attribute-defined-outside-init
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import UpdateView, DeleteView, CreateView, View

from django_tables2 import SingleTableView
from oscar.apps.dashboard.catalogue.views import CategoryListMixin
from oscar.core.loading import get_class, get_model

from django import http
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser


DeliveryZona = get_model("delivery", "DeliveryZona")
DeliveryZonaForm = get_class("dashboard.delivery.forms", "DeliveryZonaForm")
DeliveryZonesTable = get_class("dashboard.delivery.tables", "DeliveryZonesTable")
 

class DeliveryZonesView(SingleTableView):
    """
    An overview view which displays several reports about the shop.

    Supports the permission-based dashboard. It is recommended to add a
    :file:`oscar/dashboard/index_nonstaff.html` template because Oscar's
    default template will display potentially sensitive store information.
    """

    model = DeliveryZona
    table_class = DeliveryZonesTable
    context_table_name = "zones"
    template_name = "oscar/dashboard/delivery/delivery_zones.html"
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE


    # def dispatch(self, request, *args, **kwargs):
    #     return super().dispatch(request, *args, **kwargs)

    # def get(self, request, *args, **kwargs):
    #     return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Build the queryset for this list.
        """
        
        return self.model.objects.all()
    

class DeliveryZonesCreateView(CreateView):
    template_name = "oscar/dashboard/delivery/delivery_form.html"
    model = DeliveryZona
    form_class = DeliveryZonaForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Добавить новую зону доставки"
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Зона доставки успешно создана")
        return reverse("dashboard:delivery-zones")


class DeliveryZonesUpdateView(UpdateView):
    template_name = "oscar/dashboard/delivery/delivery_form.html"
    model = DeliveryZona
    form_class = DeliveryZonaForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["number"] = self.object.number
        ctx["title"] = "Обновить зону доставки '%s'" % self.object.number
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Зона доставки успешно обновлена")
        return reverse("dashboard:delivery-zones")


class DeliveryZonesDeleteView(CategoryListMixin, DeleteView):
    template_name = "oscar/dashboard/delivery/delivery_zona_delete.html"
    model = DeliveryZona

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Удалить зону доставки '%s'" % self.object.number
        ctx["number"] = self.object.number
        ctx["description"] = self.object.description
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Зона доставки успешно удалена")
        return reverse("dashboard:delivery-zones")


class DeliveryZonaView(APIView):
    """
    Return the 'delivery zona params' Only Dashboard.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]
    model = DeliveryZona

    def post(self, request, *args, **kwargs):
        try: 
            zona_id = request.POST.get('zona_id')
            zona = self.model.objects.get(number=zona_id)
            res = {
                'number': zona.number,
                'description': zona.description,
                'order_price': zona.order_price,
                'delivery_price': zona.delivery_price,
                'isAvailable': zona.isAvailable,
                'isHide': zona.isHide,
            }
            return http.JsonResponse(res, status=200)
        except Exception:
            return http.JsonResponse({"error": "Зона доставки не найдена"}, status=200)


class DeliveryZonesUpdateView(UpdateView):
    template_name = "oscar/dashboard/delivery/delivery_form.html"
    model = DeliveryZona
    form_class = DeliveryZonaForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["number"] = self.object.number
        ctx["title"] = "Обновить зону доставки '%s'" % self.object.number
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Зона доставки успешно обновлена")
        return reverse("dashboard:delivery-zones")


class DeliveryZonesHideView(UpdateView):
    model = DeliveryZona

    def post(self, request, *args, **kwargs):
        try:
            zona_id = kwargs.get('pk')
            zona = self.model.objects.get(number=zona_id)
            zona.isHide = not zona.isHide
            zona.save()
            return self.get_success_url()
        except Exception:
            return self.get_error_url()

    def get_success_url(self):
        messages.info(self.request, "Зона доставки успешно обновлена")
        return redirect("dashboard:delivery-zones")

    def get_error_url(self):
        messages.warning(self.request, "Зона доставки не была обновлена")
        return redirect("dashboard:delivery-zones")


class DeliveryZonesAvailableView(View):
    model = DeliveryZona
    
    def post(self, request, *args, **kwargs):
        try:
            zona_id = kwargs.get('pk')
            zona = self.model.objects.get(number=zona_id)
            zona.isAvailable = not zona.isAvailable
            zona.save()
            return self.get_success_url()
        except Exception:
            return self.get_error_url()

    def get_success_url(self):
        messages.info(self.request, "Зона доставки успешно обновлена")
        return redirect("dashboard:delivery-zones")

    def get_error_url(self):
        messages.warning(self.request, "Зона доставки не была обновлена")
        return redirect("dashboard:delivery-zones")


















class DeliveryStatsView(View):
    pass

class DeliveryNowView(View):
    pass

class DeliveryCouriersListView(View):
    pass

class DeliveryKitchenView(View):
    pass

class DeliveryCouriersView(View):
    pass

