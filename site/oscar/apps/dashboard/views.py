import json
import datetime as datetime_min

from datetime import datetime, timedelta
from decimal import ROUND_UP
from decimal import Decimal as D

from django.contrib import messages
from django.db.models import Avg, Count, Sum
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import TemplateView

from oscar.apps.customer.views import AccountAuthView
from oscar.apps.dashboard.orders.views import queryset_orders
from oscar.core.utils import datetime_combine
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model

RelatedFieldWidgetWrapper = get_class("dashboard.widgets", "RelatedFieldWidgetWrapper")
ConditionalOffer = get_model("offer", "ConditionalOffer")
Voucher = get_model("voucher", "Voucher")
Basket = get_model("basket", "Basket")
StockAlert = get_model("store", "StockAlert")
Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
Order = get_model("order", "Order")
Line = get_model("order", "Line")
User = get_user_model()


class IndexView(TemplateView):
    """
    An overview view which displays several reports about the shop.

    Supports the permission-based dashboard. It is recommended to add a
    :file:`oscar/dashboard/index_nonstaff.html` template because Oscar's
    default template will display potentially sensitive store information.
    """

    def get_template_names(self):
        if self.request.user.is_staff:
            return [
                "oscar/dashboard/index.html",
            ]
        else:
            return ["oscar/dashboard/index_nonstaff.html", "oscar/dashboard/index.html"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.get_stats())
        return ctx

    def get_active_vouchers(self):
        """
        Get all active vouchers. The returned ``Queryset`` of vouchers
        is filtered by end date greater then the current date.
        """
        return Voucher.objects.filter(end_datetime__gt=now())

    def get_hourly_report(self, orders, hours=24, segments=10):
        """
        Get report of order revenue split up in hourly chunks. A report is
        generated for the last *hours* (default=24) from the current time.
        The report provides ``max_revenue`` of the hourly order revenue sum,
        ``y-range`` as the labelling for the y-axis in a template and
        ``order_total_hourly``, a list of properties for hourly chunks.
        *segments* defines the number of labelling segments used for the y-axis
        when generating the y-axis labels (default=10).
        """
        # Get datetime for 24 hours ago
        start_time = now().replace(minute=0, second=0) - timedelta(hours=hours - 1)

        order_total_hourly = []
        for _ in range(0, hours, 2):
            end_time = start_time + timedelta(hours=2)
            hourly_orders = orders.filter(
                date_placed__gte=start_time, date_placed__lt=end_time
            )
            total = hourly_orders.aggregate(Sum("total"))["total__sum"] or D("0.0")
            order_total_hourly.append({"end_time": end_time, "total": total})
            start_time = end_time

        max_value = max([x["total"] for x in order_total_hourly])
        divisor = 1
        while divisor < max_value / 50:
            divisor *= 10
        max_value = (max_value / divisor).quantize(D("1"), rounding=ROUND_UP)
        max_value *= divisor
        if max_value:
            segment_size = (max_value) / D("100.0")
            for item in order_total_hourly:
                item["percentage"] = int(item["total"] / segment_size)

            y_range = []
            y_axis_steps = max_value / D(str(segments))
            for idx in reversed(range(segments + 1)):
                y_range.append(idx * y_axis_steps)
        else:
            y_range = []
            for item in order_total_hourly:
                item["percentage"] = 0

        ctx = {
            "order_total_hourly": order_total_hourly,
            "max_revenue": max_value,
            "y_range": y_range,
        }
        return ctx

    def get_days_report(self, orders, days=7, segments=10):
        """
        Get report of order revenue split up in days chunks. A report is
        generated for the last *days* (default=7 week) from the current time.
        The report provides ``max_revenue`` of the hourly order revenue sum,
        ``y-range`` as the labelling for the y-axis in a template and
        ``order_total_hourly``, a list of properties for hourly chunks.
        *segments* defines the number of labelling segments used for the y-axis
        when generating the y-axis labels (default=10).
        """
        start_time = datetime_combine(now(), datetime_min.time.max) - timedelta(
            days=days
        )

        order_total_days = []
        for _ in range(0, days, 1):
            end_time = start_time + timedelta(days=1)
            days_orders = orders.filter(
                date_placed__gte=start_time, date_placed__lt=end_time
            )
            total = days_orders.aggregate(Sum("total"))["total__sum"] or D("0.0")
            order_total_days.append({"end_time": end_time, "total": total})
            start_time = end_time

        max_value = max([x["total"] for x in order_total_days])
        divisor = 1
        while divisor < max_value / 50:
            divisor *= 10
        max_value = (max_value / divisor).quantize(D("1"), rounding=ROUND_UP)
        max_value *= divisor
        if max_value:
            segment_size = (max_value) / D("100.0")
            for item in order_total_days:
                item["percentage"] = int(item["total"] / segment_size)

            y_range = []
            y_axis_steps = max_value / D(str(segments))
            for idx in reversed(range(segments + 1)):
                y_range.append(idx * y_axis_steps)
        else:
            y_range = []
            for item in order_total_days:
                item["percentage"] = 0

        ctx = {
            "order_total_days": order_total_days,
            "max_revenue": max_value,
            "y_range": y_range,
        }
        return ctx

    def get_data(self):
        request = self.request
        prod_slug, cat_slug = request.GET.get("product"), request.GET.get("category")
        users = User.objects.all()
        staff_stores = request.staff_stores

        if prod_slug:
            prods = Product.objects.filter(slug=prod_slug)
            prod = prods.first()
            title = f"Статистика для товара '{prod.get_name()}'"
            ids = [prod.id]
        elif cat_slug:
            cat = Category.objects.get(slug=cat_slug)
            prods = Product.objects.filter(categories=cat)
            title = f"Статистика для категории '{cat.name}'"
            ids = list(prods.values_list("id", flat=True))
        else:
            prods, ids, title = Product.objects.all(), [], "Статистика"

        return {
            "title": title,
            "orders": queryset_orders(
                request=request,
                **(
                    {"product": prod}
                    if prod_slug
                    else {"category": cat} if cat_slug else {}
                ),
            ),
            "alerts": StockAlert.objects.filter(
                stockrecord__product_id__in=ids, stockrecord__store__in=staff_stores
            ),
            "baskets": Basket.objects.filter(
                lines__product_id__in=ids, status=Basket.OPEN, store__in=staff_stores
            ),
            "users": users.filter(
                baskets__lines__product_id__in=ids, baskets__store__in=staff_stores
            ).distinct(),
            "customers": users.filter(
                orders__lines__product_id__in=ids, orders__store__in=staff_stores
            ).distinct(),
            "lines": Line.objects.filter(
                product_id__in=ids, order__store__in=staff_stores
            ),
            "products": prods,
        }

    def get_stats(self):
        current_time = datetime_combine(now(), datetime_min.time.min)
        start_of_week = current_time.weekday()
        start_of_month = datetime(
            year=current_time.year,
            month=current_time.month,
            day=1,
            tzinfo=current_time.tzinfo,
        )

        datetime_day_ago = current_time
        datetime_week_ago = current_time - timedelta(days=start_of_week)
        datetime_month_ago = current_time - (current_time - start_of_month)
        datetime_7days_ago = current_time - timedelta(days=7)
        datetime_30days_ago = current_time - timedelta(days=30)

        data = self.get_data()

        orders = data["orders"]
        alerts = data["alerts"]
        baskets = data["baskets"]
        users = data["users"]
        customers = data["customers"]
        lines = data["lines"]
        products = data["products"]

        orders_last_day = orders.filter(date_placed__gt=datetime_day_ago)
        orders_last_week = orders.filter(date_placed__gt=datetime_week_ago)
        orders_last_month = orders.filter(date_placed__gt=datetime_month_ago)

        orders_last_7days = orders.filter(date_placed__gt=datetime_7days_ago)
        orders_last_30days = orders.filter(date_placed__gt=datetime_30days_ago)

        open_alerts = alerts.filter(status=StockAlert.OPEN)
        closed_alerts = alerts.filter(status=StockAlert.CLOSED)

        total_lines_last_day = lines.filter(order__in=orders_last_day).count()
        total_lines_last_week = lines.filter(order__in=orders_last_week).count()
        total_lines_last_month = lines.filter(order__in=orders_last_month).count()

        total_lines_last_7days = lines.filter(order__in=orders_last_7days).count()
        total_lines_last_30days = lines.filter(order__in=orders_last_30days).count()

        stats = {
            "title": data["title"],
            "current_time": current_time,
            "start_of_week": datetime_week_ago,
            "start_of_month": start_of_month,
            "time_7days_ago": datetime_7days_ago,
            "time_30days_ago": datetime_30days_ago,
            "hourly_report_dict": self.get_hourly_report(orders),
            "week_report_dict": self.get_days_report(orders, 7),
            "month_report_dict": self.get_days_report(orders, 30),
            "total_orders_last_day": orders_last_day.count(),
            "total_lines_last_day": total_lines_last_day,
            "average_order_costs_day": orders_last_day.aggregate(Avg("total"))[
                "total__avg"
            ]
            or D("0.00"),
            "total_revenue_last_day": orders_last_day.aggregate(Sum("total"))[
                "total__sum"
            ]
            or D("0.00"),
            "total_customers_last_day": customers.filter(
                date_joined__gt=datetime_day_ago,
            ).count(),
            "total_users_last_day": users.filter(
                date_joined__gt=datetime_day_ago,
            ).count(),
            "total_open_baskets_last_day": baskets.filter(
                date_created__gt=datetime_day_ago
            ).count(),
            "total_open_baskets_last_week": baskets.filter(
                date_created__gt=datetime_week_ago
            ).count(),
            "total_orders_last_week": orders_last_week.count(),
            "total_lines_last_week": total_lines_last_week,
            "average_order_costs_week": orders_last_week.aggregate(Avg("total"))[
                "total__avg"
            ]
            or D("0.00"),
            "total_revenue_last_week": orders_last_week.aggregate(Sum("total"))[
                "total__sum"
            ]
            or D("0.00"),
            "total_customers_last_week": customers.filter(
                date_joined__gt=datetime_week_ago,
            ).count(),
            "total_users_last_week": users.filter(
                date_joined__gt=datetime_week_ago,
            ).count(),
            "total_lines_last_7days": total_lines_last_7days,
            "total_orders_last_7days": orders_last_7days.count(),
            "average_order_costs_7days": orders_last_7days.aggregate(Avg("total"))[
                "total__avg"
            ]
            or D("0.00"),
            "total_revenue_last_7days": orders_last_7days.aggregate(Sum("total"))[
                "total__sum"
            ]
            or D("0.00"),
            "total_customers_last_7days": customers.filter(
                date_joined__gt=datetime_7days_ago,
            ).count(),
            "total_open_baskets_last_7days": baskets.filter(
                date_created__gt=datetime_7days_ago
            ).count(),
            "total_orders_last_month": orders_last_month.count(),
            "total_lines_last_month": total_lines_last_month,
            "average_order_costs_month": orders_last_month.aggregate(Avg("total"))[
                "total__avg"
            ]
            or D("0.00"),
            "total_revenue_last_month": orders_last_month.aggregate(Sum("total"))[
                "total__sum"
            ]
            or D("0.00"),
            "total_users_last_month": users.filter(
                date_joined__gt=datetime_month_ago,
            ).count(),
            "total_customers_last_month": customers.filter(
                date_joined__gt=datetime_month_ago,
            ).count(),
            "total_open_baskets_last_month": baskets.filter(
                date_created__gt=datetime_month_ago
            ).count(),
            "total_orders_last_30days": orders_last_30days.count(),
            "total_lines_last_30days": total_lines_last_30days,
            "average_order_costs_30days": orders_last_30days.aggregate(Avg("total"))[
                "total__avg"
            ]
            or D("0.00"),
            "total_revenue_last_30days": orders_last_30days.aggregate(Sum("total"))[
                "total__sum"
            ]
            or D("0.00"),
            "total_customers_last_30days": customers.filter(
                date_joined__gt=datetime_30days_ago,
            ).count(),
            "total_open_baskets_last_30days": baskets.filter(
                date_created__gt=datetime_30days_ago
            ).count(),
            "total_products": products.count(),
            "total_open_stock_alerts": open_alerts.count(),
            "total_closed_stock_alerts": closed_alerts.count(),
            "total_users": users.count(),
            "total_customers_2orders": customers.annotate(order_count=Count("orders"))
            .filter(order_count__gte=2)
            .count(),
            "total_customers_5orders": customers.annotate(order_count=Count("orders"))
            .filter(order_count__gte=5)
            .count(),
            "total_customers": customers.count(),
            "guest_baskets": baskets.filter(owner__isnull=True).count(),
            "customers_baskets": baskets.filter(owner__isnull=False).count(),
            "total_open_baskets": baskets.count(),
            "total_orders": orders.count(),
            "total_lines": lines.count(),
            "total_revenue": orders.aggregate(Sum("total"))["total__sum"] or D("0.00"),
            "order_status_breakdown": orders.order_by("status")
            .values("status")
            .annotate(freq=Count("id")),
        }

        if self.request.user.is_staff:
            stats.update(
                offer_maps=(
                    ConditionalOffer.objects.filter(end_datetime__gt=now())
                    .values("offer_type")
                    .annotate(count=Count("id"))
                    .order_by("offer_type")
                ),
                total_vouchers=self.get_active_vouchers().count(),
            )
        return stats


class PopUpWindowMixin:
    @property
    def is_popup(self):
        return self.request.GET.get(
            RelatedFieldWidgetWrapper.IS_POPUP_VAR,
            self.request.POST.get(RelatedFieldWidgetWrapper.IS_POPUP_VAR),
        )

    @property
    def is_popup_var(self):
        return RelatedFieldWidgetWrapper.IS_POPUP_VAR

    def add_success_message(self, message):
        if not self.is_popup:
            messages.info(self.request, message)


class PopUpWindowCreateUpdateMixin(PopUpWindowMixin):
    @property
    def to_field(self):
        return self.request.GET.get(
            RelatedFieldWidgetWrapper.TO_FIELD_VAR,
            self.request.POST.get(RelatedFieldWidgetWrapper.TO_FIELD_VAR),
        )

    @property
    def to_field_var(self):
        return RelatedFieldWidgetWrapper.TO_FIELD_VAR

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if self.is_popup:
            ctx["to_field"] = self.to_field
            ctx["to_field_var"] = self.to_field_var
            ctx["is_popup"] = self.is_popup
            ctx["is_popup_var"] = self.is_popup_var

        return ctx


class PopUpWindowCreateMixin(PopUpWindowCreateUpdateMixin):
    def popup_response(self, obj):
        if self.to_field:
            attr = str(self.to_field)
        else:
            attr = obj._meta.pk.attname
        value = obj.serializable_value(attr)
        popup_response_data = json.dumps(
            {
                "value": str(value),
                "obj": str(obj),
            }
        )
        return TemplateResponse(
            self.request,
            "oscar/dashboard/widgets/popup_response.html",
            {
                "popup_response_data": popup_response_data,
            },
        )


class PopUpWindowUpdateMixin(PopUpWindowCreateUpdateMixin):
    def popup_response(self, obj):
        opts = obj._meta
        if self.to_field:
            attr = str(self.to_field)
        else:
            attr = opts.pk.attname
        # Retrieve the `object_id` from the resolved pattern arguments.
        value = self.request.resolver_match.kwargs["pk"]
        new_value = obj.serializable_value(attr)
        popup_response_data = json.dumps(
            {
                "action": "change",
                "value": str(value),
                "obj": str(obj),
                "new_value": str(new_value),
            }
        )
        return TemplateResponse(
            self.request,
            "oscar/dashboard/widgets/popup_response.html",
            {
                "popup_response_data": popup_response_data,
            },
        )


class PopUpWindowDeleteMixin(PopUpWindowMixin):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if self.is_popup:
            ctx["is_popup"] = self.is_popup
            ctx["is_popup_var"] = self.is_popup_var

        return ctx

    def delete(self, request, *args, **kwargs):
        """
        Calls the delete() method on the fetched object and then
        redirects to the success URL, or closes the popup, it it is one.
        """
        obj = self.get_object()

        response = super().delete(request, *args, **kwargs)

        if self.is_popup:
            obj_id = obj.pk
            popup_response_data = json.dumps(
                {
                    "action": "delete",
                    "value": str(obj_id),
                }
            )
            return TemplateResponse(
                request,
                "oscar/dashboard/widgets/popup_response.html",
                {
                    "popup_response_data": popup_response_data,
                },
            )
        else:
            return response

    def post(self, request, *args, **kwargs):
        """
        Calls the delete() method on the fetched object and then
        redirects to the success URL, or closes the popup, it it is one.
        """
        return self.delete(request, *args, **kwargs)


class LoginView(AccountAuthView):
    template_name = "oscar/dashboard/login.html"

    def get_auth_success_url(self, form):
        redirect_url = self.request.POST.get("redirect_url")
        if redirect_url:
            return redirect_url

        return reverse_lazy("dashboard:index")
