import datetime as datetime_min

from django.conf import settings
from django.core.cache import cache
from django.db.models import Sum
from django.utils.timezone import now

from oscar.core.utils import datetime_combine
from oscar.core.loading import get_model

Order = get_model("order", "Order")

class DashboardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/dashboard'):
            return self.get_response(request)

        # Получаем данные из кэша или базы
        revenue_today = cache.get('revenue_today')
        if revenue_today is None:
            revenue_today = (
                Order.objects.filter(date_placed__gt=datetime_combine(now(), datetime_min.time.min))
                .aggregate(total_revenue=Sum('total'))['total_revenue'] or 0
            )
            cache.set("revenue_today", revenue_today, 120)
        
        request.revenue_today = revenue_today
        request.active_orders = Order.objects.filter(status__in=settings.ORDER_ACTIVE_STATUSES).count()

        return self.get_response(request)

    def process_template_response(self, request, response):
        if not request.path.startswith('/dashboard') or not hasattr(response, "context_data"):
            return response

        # Убедимся, что context_data существует
        response.context_data = response.context_data or {}
        response.context_data.setdefault("revenue_today", getattr(request, "revenue_today", 0))
        response.context_data.setdefault("active_orders", getattr(request, "active_orders", 0))

        return response