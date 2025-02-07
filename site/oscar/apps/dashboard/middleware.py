import datetime as datetime_min

from django.conf import settings
from django.core.cache import cache
from django.db.models import Sum
from django.utils.timezone import now

from oscar.core.utils import datetime_combine
from oscar.core.loading import get_model

Store = get_model("store", "Store")
Order = get_model("order", "Order")


class DashboardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/dashboard")and request.user.is_authenticated:
            return self.get_response(request)

        stores = cache.get("stores")
        if stores is None:
            stores = Store.objects.prefetch_related("addresses", "users").all()
            cache.set("stores", stores, 21600)

        # Определяем магазины, с которыми работаем
        if request.user.has_perm("user.full_access") or request.user.is_superuser:
            request.staff_stores = stores
        else:
            request.staff_stores = stores.filter(users=request.user)

        # Получаем выручку для всех магазинов
        request.revenue_today = self.get_revenue_for_stores(request.staff_stores)

        # Получаем заказы
        request.no_finish_orders = self.get_orders_for_stores(request.staff_stores)
        request.active_orders = self.get_active_orders_for_stores(request.staff_stores)

        return self.get_response(request)

    def get_revenue_for_stores(self, stores):
        """
        Получает выручку для всех магазинов и кэширует её.
        """
        revenue_today = 0
        current_time = now()
        for store in stores:
            store_revenue_today = cache.get(f"revenue_today_{store.id}")
            if store_revenue_today is None:
                store_revenue_today = (
                    Order.objects.filter(
                        date_placed__gt=datetime_combine(current_time, datetime_min.time.min),
                        store=store,
                    ).aggregate(total_revenue=Sum("total"))["total_revenue"]
                    or 0
                )
                cache.set(f"revenue_today_{store.id}", store_revenue_today, 180)

            revenue_today += store_revenue_today
        return revenue_today

    def get_orders_for_stores(self, stores):
        """
        Получает заказы с учётом того, что они не завершены.
        """
        return Order.objects.filter(date_finish__isnull=True, store__in=stores)

    def get_active_orders_for_stores(self, stores):
        """
        Получает активные заказы для указанных магазинов.
        """
        return Order.objects.filter(
            date_finish__isnull=True,
            status__in=settings.ORDER_ACTIVE_STATUSES,
            store__in=stores,
        ).count()

    def process_template_response(self, request, response):
        if not request.path.startswith("/dashboard") or not hasattr(
            response, "context_data"
        ):
            return response

        # Убедимся, что context_data существует
        response.context_data = response.context_data or {}
        response.context_data.setdefault(
            "revenue_today", getattr(request, "revenue_today", 0)
        )
        response.context_data.setdefault(
            "active_orders", getattr(request, "active_orders", 0)
        )

        return response
