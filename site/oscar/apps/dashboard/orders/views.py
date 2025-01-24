# pylint: disable=attribute-defined-outside-init

import csv
import io
import datetime
import logging

from decimal import Decimal as D
from decimal import InvalidOperation
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django_tables2 import SingleTableView, RequestConfig
from django.db.models import Count, Sum, fields, F, Max, ExpressionWrapper, DurationField, When, Value, Case, Avg, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.generic import DetailView, FormView, UpdateView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.timezone import now
from django.template.loader import render_to_string

from oscar.views.generic import BulkEditMixin
from oscar.apps.order import exceptions as order_exceptions
from oscar.apps.payment.exceptions import PaymentError
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model
from oscar.core.utils import datetime_combine, format_datetime
from oscar.views import sort_queryset

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication


logger = logging.getLogger("oscar.dashboard")

User = get_user_model()

Order = get_model("order", "Order")
OrderNote = get_model("order", "OrderNote")
Line = get_model("order", "Line")
ShippingAddress = get_model("order", "ShippingAddress")
ShippingEventType = get_model("order", "ShippingEventType")
PaymentEventType = get_model("order", "PaymentEventType")
Basket = get_model("basket", "Basket")
Store = get_model("store", "Store")
StockAlert = get_model("store", "StockAlert")
Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
Transaction = get_model("payment", "Transaction")
SourceType = get_model("payment", "SourceType")
Voucher = get_model("voucher", "Voucher")

EventHandlerMixin = get_class("order.mixins", "EventHandlerMixin")

OrderStatsForm = get_class("dashboard.orders.forms", "OrderStatsForm")
OrderSearchForm = get_class("dashboard.orders.forms", "OrderSearchForm")
ActiveOrderSearchForm = get_class("dashboard.orders.forms", "ActiveOrderSearchForm")
OrderNoteForm = get_class("dashboard.orders.forms", "OrderNoteForm")
ShippingAddressForm = get_class("dashboard.orders.forms", "ShippingAddressForm")
OrderStatusForm = get_class("dashboard.orders.forms", "OrderStatusForm")

OrderTable = get_class("dashboard.orders.tables", "OrderTable")
ProductSearchForm = get_class("dashboard.catalogue.forms", "ProductSearchForm")


def queryset_orders(user, product=None, category=None):
    """
    Returns a queryset of all orders that a user is allowed to access.
    A staff user may access all orders.
    To allow access to an order for a non-staff user, at least one line's
    store has to have the user in the store's list.
    """
    queryset = Order._default_manager.select_related(
        "shipping_address",
        "user",
        "store",
    ).prefetch_related("lines", "status_changes", "sources", "payment_events", "shipping_events")

    if product:
        queryset = queryset.filter(lines__product=product)

    if category:
        queryset = queryset.filter(lines__product__categories=category)

    if user.is_superuser:
        return queryset
    else:
        stores = Store._default_manager.filter(users=user)
        return queryset.filter(lines__store__in=stores).distinct()

def get_order_or_404(user, number):
    try:
        return queryset_orders(user=user).get(number=number)
    except ObjectDoesNotExist:
        raise Http404()


class OrderStatsView(FormView):
    """
    Dashboard view for order statistics.
    Supports the permission-based dashboard.
    """

    template_name = "oscar/dashboard/orders/statistics.html"
    form_class = OrderStatsForm
        
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def form_valid(self, form):
        filters, excludes = form.get_filters()
        ctx = self.get_context_data(form=form, filters=filters, excludes=excludes)
        return self.render_to_response(ctx)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["data"] = self.request.GET
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = kwargs.get("form", self.form_class)
        filters = kwargs.get("filters", {})

        # if filters.get('date_placed__range') is not None:
        #     filters['date_placed__range'] = (datetime_combine(filters['date_placed__range'][0], datetime.time.min), datetime_combine(filters['date_placed__range'][1], datetime.time.min))
        # elif filters.get('date_placed__gte') is not None:
        #     filters['date_placed__gte'] = (datetime_combine(filters['date_placed__gte'][0], datetime.time.min),)
        # elif filters.get('date_placed__lte') is not None:
        #     filters['date_placed__lte'] = (datetime_combine(filters['date_placed__lte'][0], datetime.time.min),)
    
        excludes = kwargs.get("excludes", {})
        ctx.update(self.get_stats(filters, excludes))
        ctx["title"] = kwargs["form"].get_filter_description()
        ctx["search_filters"] = kwargs["form"].get_search_filters()
        ctx["active_tab"] = "day"
        return ctx

    def get_report(self, orders, start, end, range_type):

        start_time = start
        if range_type == 'days':
            range_time = (end - start).days
        elif range_type == 'weeks':
            start_time = start - datetime.timedelta(days=start.weekday())
            end_sunday = end + datetime.timedelta(days=(6 - end.weekday()))
            range_time = (end_sunday - start_time).days // 7
        elif range_type == 'months':
            start_time = start_time.replace(day=1)
            diff = relativedelta(end, start)
            range_time = diff.years * 12 + diff.months + (1 if diff.days > 0 else 0)
        elif range_type == 'years':
            start_time = start.replace(month=1, day=1)
            range_time = end.year - start.year + 1
        else:
            raise ValueError("Invalid range_type. Must be 'days', 'weeks', 'months', or 'years'.")

        range_time = max(1, range_time)

        order_data = {}
        order_labels = []
        order_total = []
        order_count = []

        for _ in range(range_time):
            if range_type == 'days':
                end_time = start_time + relativedelta(days=1)
            elif range_type == 'weeks':
                end_time = start_time + relativedelta(days=7)
            elif range_type == 'months':
                end_time = start_time + relativedelta(months=1)
            elif range_type == 'years':
                end_time = start_time + relativedelta(years=1) 
            else: 
                end_time = start_time

            report_orders = orders.filter(date_placed__gte=start_time, date_placed__lt=end_time)
            total = report_orders.aggregate(Sum("total"))["total__sum"] or D("0.0")
            count = report_orders.count()
            order_count.append(count) 
            order_total.append(int(total))
            if range_type == 'days':
                order_labels.append(start_time.strftime('%d.%m'))
            elif range_type == 'weeks':
                order_labels.append(start_time.strftime('%d.%m') + "-" + end_time.strftime('%d.%m'))
            elif range_type == 'months':
                order_labels.append(start_time.strftime('%m.%Y'))
            else:
                order_labels.append(start_time.strftime('%Y'))

            start_time = end_time

        order_data["labels"] = order_labels
        order_data["datasets"] = [
            {
                "label": "Сумма заказов", 
                "data": order_total, 
                "backgroundColor": ['rgba(54, 162, 235, 0.3)'], 
                "borderColor": ['rgb(54, 162, 235)'], 
                "borderWidth": 1,
                "yAxisID": 'y',
            },
            {
                "label": "Кол-во заказов",
                "data": order_count, 
                "backgroundColor": ['rgba(153, 102, 255, 0.3)'], 
                "borderColor": ['rgb(153, 102, 255)'],
                "borderWidth": 1,
                "yAxisID": 'y1',
            }
        ]
        
        return order_data, sum(order_count) > 0

    def get_data(self, filters, excludes):
        orders = queryset_orders(user=self.request.user).filter(**filters).exclude(**excludes)
        
        if filters.get('date_placed__range') is not None:
            start_date, end_date = filters['date_placed__range']
            users = User.objects.filter(date_joined__range=[start_date, end_date])
            alerts = StockAlert.objects.filter(date_created__range=[start_date, end_date])
            baskets = Basket.objects.filter(status=Basket.OPEN, date_created__range=[start_date, end_date])
            products = Product.objects.filter(date_created__range=[start_date, end_date])
            lines = Line.objects.filter(order__in=orders)
        elif filters.get('date_placed__gte') is not None:
            start_date = filters['date_placed__gte']
            users = User.objects.filter(date_joined__gte=start_date)
            alerts = StockAlert.objects.filter(date_created__gte=start_date)
            baskets = Basket.objects.filter(status=Basket.OPEN, date_created__gte=start_date)
            products = Product.objects.filter(date_created__gte=start_date)
            lines = Line.objects.filter(order__in=orders)
        elif filters.get('date_placed__lte') is not None:
            end_date = filters['date_placed__lte']
            users = User.objects.filter(date_joined__lte=end_date)
            alerts = StockAlert.objects.filter(date_created__lte=end_date)
            baskets = Basket.objects.filter(status=Basket.OPEN, date_created__lte=end_date)
            products = Product.objects.filter(date_created__lte=end_date)
            lines = Line.objects.filter(order__in=orders)
        else:     
            users = User.objects.all()
            alerts = StockAlert.objects.all()
            baskets = Basket.objects.filter(status=Basket.OPEN)
            products = Product.objects.all()
            lines = Line.objects.filter(order__in=orders)

        data = {
            "orders": orders,
            "alerts": alerts,
            "baskets": baskets,
            "users": users,
            "customers": users.filter(orders__isnull=False).distinct(),
            "lines": lines,
            "products": products,
        }

        return data
    
    def get_stats(self, filters, excludes):
        # Установка начальной и конечной даты
        start_date, end_date = None, now()

        # Определение диапазонов дат
        if 'date_placed__range' in filters:
            start_date, end_date = filters['date_placed__range']
        elif 'date_placed__gte' in filters:
            start_date = filters['date_placed__gte']
        elif 'date_placed__lte' in filters:
            end_date = filters['date_placed__lte']

        # Получение данных
        data = self.get_data(filters, excludes)
        orders = data['orders']
        alerts = data['alerts']
        baskets = data['baskets']
        users = data['users']
        customers = data['customers']
        lines = data['lines']
        products = data['products']

        # Определение начальной даты при отсутствии
        if start_date is None:
            ord = orders.order_by('date_placed').first()
            if ord is not None:
                start_date = ord.date_placed
            else:
                start_date = end_date - datetime.timedelta(days=90)

        start_date = datetime_combine(start_date, datetime.time.min)
        end_date = datetime_combine(end_date, datetime.time.max)

        # Установка стартовых дат для различных интервалов
        start_dates = {
            "days": max(start_date, end_date - datetime.timedelta(days=60)),
            "weeks": max(start_date, end_date - datetime.timedelta(weeks=20)),
            "months": max(start_date, end_date - relativedelta(months=12)),
            "years": max(start_date, end_date - relativedelta(years=3)),
        }

        # Создание словаря с результатами
        stats = {
            "start_date_days": start_dates["days"],
            "start_date_weeks": start_dates["weeks"],
            "start_date_months": start_dates["months"],
            "start_date_years": start_dates["years"],
            "start_date": start_date,
            "end_date": end_date,
            "report_datas": [],
            "top_products_names": [],
            "top_products_quantities": [],
            "top_products_sums": [],
        }

        def aggregate_orders(queryset, field, operation, default=D('0.00')):
            result = queryset.aggregate(result=operation(field))['result']
            return result or default

        def count_customers_with_orders(customers, min_orders):
            return customers.annotate(order_count=Count('orders')).filter(order_count__gte=min_orders, date_joined__range=(start_date, end_date)).count()

        for period, start in start_dates.items():
            orders_period = orders.filter(date_placed__range=(start_date, end_date))
            lines_period = lines.filter(order__in=orders_period)

            top_products = (
                lines_period
                .values('product', 'name')
                .annotate(total_quantity=Sum('quantity'), total_sum=Sum('line_price'))
                .order_by('-total_quantity')[:5]
            )

            revenue = aggregate_orders(orders_period, 'total', Sum)
            revenue_offline = aggregate_orders(orders_period.filter(site="Эвотор"), 'total', Sum)
            revenue_online = revenue - revenue_offline

            discount = (
                aggregate_orders(orders_period, 'lines__line_price_before_discounts', Sum)
                - revenue
            )
            discount_offline = (
                aggregate_orders(orders_period.filter(site="Эвотор"), 'lines__line_price_before_discounts', Sum)
                - revenue_offline
            )
            discount_online = discount - discount_offline

            stats.update({
                f"orders_{period}": orders_period.count(),
                f"orders_offline_{period}": orders_period.filter(site="Эвотор").count(),
                f"orders_online_{period}": orders_period.exclude(site="Эвотор").count(),

                f"revenue_{period}": revenue,
                f"revenue_offline_{period}": revenue_offline,
                f"revenue_online_{period}": revenue_online,

                f"discount_{period}": discount,
                f"discount_offline_{period}": discount_offline,
                f"discount_online_{period}": discount_online,

                f"average_costs_{period}": aggregate_orders(orders_period, 'total', Avg),
                f"average_offline_costs_{period}": aggregate_orders(orders_period.filter(site="Эвотор"), 'total', Avg),
                f"average_online_costs_{period}": aggregate_orders(orders_period.exclude(site="Эвотор"), 'total', Avg),

                f"alerts_{period}": alerts.filter(date_created__range=(start_date, end_date)).count(),
                f"baskets_{period}": baskets.filter(date_created__range=(start_date, end_date)).count(),
                f"users_{period}": users.filter(date_joined__range=(start_date, end_date)).count(),

                f"customers_{period}": customers.filter(date_joined__range=(start_date, end_date)).count(),
                f"customers_2orders_{period}": count_customers_with_orders(customers, 2),
                f"customers_5orders_{period}": count_customers_with_orders(customers, 5),

                f"lines_{period}": lines_period.count(),
                f"lines_offline_{period}": lines_period.filter(order__site="Эвотор").count(),
                f"lines_online_{period}": lines_period.exclude(order__site="Эвотор").count(),

                f"orders_discount_{period}": orders_period.filter(~Q(lines__line_price_before_discounts=F('lines__line_price'))).distinct().count(),
                f"orders_offline_discount_{period}": orders_period.filter(~Q(lines__line_price_before_discounts=F('lines__line_price')), site="Эвотор").distinct().count(),
                f"orders_online_discount_{period}": orders_period.filter(~Q(lines__line_price_before_discounts=F('lines__line_price'))).exclude(site="Эвотор").distinct().count(),

                f"lines_discount_{period}": lines_period.filter(~Q(line_price_before_discounts=F('line_price'))).count(),
                f"lines_offline_discount_{period}": lines_period.filter(~Q(line_price_before_discounts=F('line_price')), order__site="Эвотор").count(),
                f"lines_online_discount_{period}": lines_period.filter(~Q(line_price_before_discounts=F('line_price'))).exclude(order__site="Эвотор").count(),

                f"products_{period}": products.filter(date_created__range=(start_date, end_date)).count(),
                f"top_products_{period}": top_products,
                f"order_status_breakdown_{period}": orders_period.order_by("status").values("status").annotate(freq=Count("id")),

            })

            stats["top_products_names"].append([product['name'] for product in top_products])
            stats["top_products_quantities"].append([product['total_quantity'] for product in top_products])
            stats["top_products_sums"].append([int(product['total_sum']) for product in top_products])

            report, stats[f"report_exist_{period}"] = self.get_report(orders, start, end_date, period)
            stats["report_datas"].append(report)

        return stats


class OrderListView(EventHandlerMixin, BulkEditMixin, SingleTableView):
    """
    Dashboard view for a list of orders.
    Supports the permission-based dashboard.
    """
    model = Order
    template_name = "oscar/dashboard/orders/order_list.html"
    form_class = OrderSearchForm
    table_class = OrderTable
    context_table_name = "orders"
    actions = ("download_selected_orders", "change_order_statuses")

    CSV_COLUMNS = {
        "number": "Номер заказа",
        "total": "Стоимость заказа",
        "shipping_charge": "Стоимость доставки",
        "shipping_method": "Метод доставки",
        "status": "Последний статус",
        "date_placed": "Дата создания заказа",
        "date_finish": "Дата завершения заказа",
        "order_time": "Дата заказа",
        "num_items": "Количество товаров",
        "items": "Товары",
        "customer": "Клиент",
        "shipping_address_name": "Адрес доставки",
    }

    def get_table_pagination(self, table):
        # return dict(per_page=settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE)
        return dict(per_page=settings.OSCAR_ORDERS_PER_PAGE)

    def dispatch(self, request, *args, **kwargs):
        # base_queryset is equal to all orders the user is allowed to access
        self.base_queryset = queryset_orders(user=request.user).annotate(
            source=Max("sources__reference"),
            amount_paid=Sum("sources__amount_debited") - Sum("sources__amount_refunded"),
            paid=F("sources__paid"),
            before_order=Case(
                When(date_finish__isnull=True, then=ExpressionWrapper(F('order_time') - now(), output_field=DurationField())),
                default=Value(None),
                output_field=DurationField()
            )
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if (
            "order_number" in request.GET
            and request.GET.get("response_format", "html") == "html"
        ):
            # Redirect to Order detail page if valid order number is given
            try:
                order = self.base_queryset.get(number=request.GET["order_number"])
            except Order.DoesNotExist:
                pass
            else:
                return redirect("dashboard:order-detail", number=order.number)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Build the queryset for this list.
        """
        queryset = sort_queryset(
            self.base_queryset, self.request, ["number", "total", "-date_placed"]
        ).order_by(
            "-date_placed"
        )

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data["store"]:
            queryset = queryset.filter(
                store__code=data["store"]
            )

        if data["is_online"] and not data["is_offine"]:
            queryset = queryset.exclude(site__in=settings.OFFLINE_ORDERS)
        
        if not data["is_online"] and data["is_offine"]:
            queryset = queryset.filter(site__in=settings.OFFLINE_ORDERS)

        if data["order_number"]:
            queryset = queryset.filter(
                number__istartswith=data["order_number"]
            )

        if data["username"]:
            queryset = queryset.filter(user__username__istartswith=data["username"]).distinct()

        if data["product_name"]:
            queryset = queryset.filter(
                lines__name__istartswith=data["product_name"]
            ).distinct()

        if data["article"]:
            queryset = queryset.filter(lines__article=data["article"])

        if data["evotor_code"]:
            queryset = queryset.filter(lines__evotor_code=data["evotor_code"])

        if data["date_from"] and data["date_to"]:
            date_to = datetime_combine(data["date_to"], datetime.time.max)
            date_from = datetime_combine(data["date_from"], datetime.time.min)
            queryset = queryset.filter(
                date_placed__gte=date_from, date_placed__lt=date_to
            )
        elif data["date_from"]:
            date_from = datetime_combine(data["date_from"], datetime.time.min)
            queryset = queryset.filter(date_placed__gte=date_from)
        elif data["date_to"]:
            date_to = datetime_combine(data["date_to"], datetime.time.max)
            queryset = queryset.filter(date_placed__lt=date_to)

        if data["voucher"]:
            queryset = queryset.filter(
                discounts__voucher_code=data["voucher"]
            ).distinct()

        if data["payment_method"]:
            queryset = queryset.filter(
                sources__source_type__code=data["payment_method"]
            ).distinct()

        if data["status"]:
            queryset = queryset.filter(status=data["status"])

        return queryset.annotate(
            source=Max("sources__reference"),
            amount_paid=Sum("sources__amount_debited") - Sum("sources__amount_refunded"),
            paid=F("sources__paid"),
            before_order=Case(
                When(date_finish__isnull=True, then=ExpressionWrapper(F('order_time') - now(), output_field=DurationField())),
                default=Value(None),
                output_field=DurationField()
            )
        )

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        filtered_data = {key: value for key, value in self.form.cleaned_data.items() if key != 'response_format'}

        if self.form.is_valid() and any(filtered_data.values()):
            table.caption = "Результаты поиска: %s" % self.object_list.count()

        return table
    
    def get_search_filter_descriptions(self):
        """Describe the filters used in the search.

        These are user-facing messages describing what filters
        were used to filter orders in the search query.

        Returns:
            list of unicode messages

        """
        descriptions = []

        # Attempt to retrieve data from the submitted form
        # If the form hasn't been submitted, then `cleaned_data`
        # won't be set, so default to None.
        data = getattr(self.form, "cleaned_data", None)

        if data is None:
            return descriptions

        if data.get("order_number"):
            descriptions.append((
                ('Номер заказа начинается с "{order_number}"').format(
                    order_number=data["order_number"]
                ), (("order_number", data["order_number"]),)
            ))

        if data.get("username"):
            descriptions.append((
                ('Номер клиента совпадает с "{customer_name}"').format(
                    customer_name=data["username"]
                ), (("username", data["username"]),)
            ))

        if data.get("product_name"):
            descriptions.append((
                ('Название товара соответствует "{product_name}"').format(
                    product_name=data["product_name"]
                ), (("product_name", data["product_name"]),)
            ))

        if data.get("article"):
            descriptions.append((
                # Translators: "article" means "universal product code" and it is
                # used to uniquely identify a product in an online store.
                # "Item" in this context means an item in an order placed
                # in an online store.
                ('Включает товар с артикулом "{article}"').format(article=data["article"]), (("article", data["article"]),)
            ))

        if data.get("evotor_code"):
            descriptions.append((
                # Translators: "SKU" means "stock keeping unit" and is used to
                # identify products that can be shipped from an online store.
                # A "store" is a company that ships items to users who
                # buy things in an online store.
                ('Включает товар с артикулом партнера. "{evotor_code}"').format(
                    evotor_code=data["evotor_code"]
                ), (("evotor_code", data["evotor_code"]),)
            ))

        if data.get("date_from") and data.get("date_to"):
            descriptions.append((
                # Translators: This string refers to orders in an online
                # store that were made within a particular date range.
                ("Размещено между {start_date} и {end_date}").format(
                    start_date=data["date_from"], end_date=data["date_to"]
                ), (("date_from", data["date_from"]), ("date_to", data["date_to"]))
            ))

        elif data.get("date_from"):
            descriptions.append((
                # Translators: This string refers to orders in an online store
                # that were made after a particular date.
                ("Размещено после {start_date}").format(start_date=data["date_from"]), (("date_from", data["date_from"]),)
            ))

        elif data.get("date_to"):
            end_date = data["date_to"] + datetime.timedelta(days=1)
            descriptions.append((
                # Translators: This string refers to orders in an online store
                # that were made before a particular date.
                ("Размещено до {end_date}").format(end_date=end_date), (("date_to", data["date_to"]),)
            ))

        if data.get("voucher"):
            descriptions.append((
                # Translators: A "voucher" is a coupon that can be applied to
                # an order in an online store in order to receive a discount.
                # The voucher "code" is a string that users can enter to
                # receive the discount.
                ('Использованный промокод "{voucher_code}"').format(
                    voucher_code=data["voucher"]
                ), (("voucher", data["voucher"]),)
            ))

        if data.get("is_online") and not data.get("is_offine"):
            descriptions.append((
                ('Онлайн заказы'), (("is_online", True),)
            ))

        if not data.get("is_online") and data.get("is_offine"):
            descriptions.append((
                ('Эвотор заказы'), (("is_offline", True),)
            ))

        if data.get("payment_method"):
            payment_type = SourceType.objects.get(code=data["payment_method"])
            descriptions.append((
                # Translators: A payment method is a way of paying for an
                # item in an online store.  For example, a user can pay
                # with a credit card or PayPal.
                ("Оплачено с помощью {payment_method}").format(
                    payment_method=payment_type.name
                ), (("payment_method", data["payment_method"]),)
            ))

        if data.get("status"):
            descriptions.append((
                # Translators: This string refers to an order in an
                # online store.  Some examples of order status are
                # "purchased", "cancelled", or "refunded".
                ("Статус заказа {order_status}").format(order_status=data["status"]), (("status", data["status"]),)
            ))

        return descriptions

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        ctx["order_statuses"] = Order.all_statuses()
        ctx["search_filters"] = self.get_search_filter_descriptions()
        ctx["title"] = "Все заказы"
        return ctx

    def is_csv_download(self):
        return self.request.GET.get("response_format", None) == "csv"

    def get_paginate_by(self, queryset):
        return None if self.is_csv_download() else self.paginate_by

    def render_to_response(self, context, **response_kwargs):
        if self.is_csv_download():
            return self.download_selected_orders(self.request, context["object_list"])
        return super().render_to_response(context, **response_kwargs)

    def get_download_filename(self, request):
        return "orders.csv"

    def get_row_values(self, order):
        formatted_items = [
            f"{item.name}({item.quantity})"
            for item in order.lines.all()
        ]
        row = {
            "number": order.number,
            "total": order.total,
            "shipping_charge": order.shipping,
            "shipping_method": order.shipping_method,
            "status": order.status,
            "date_placed": format_datetime(order.date_placed, "DATETIME_FORMAT"),
            "date_finish": format_datetime(order.date_finish, "DATETIME_FORMAT") if order.date_finish else "",
            "order_time": format_datetime(order.order_time, "DATETIME_FORMAT"),
            "num_items": order.num_items,
            "items": " ".join(formatted_items),
            "customer": order.user.username,
            "shipping_address_name": order.shipping_address.line1 if order.shipping_address else "",
        }
        return row

    def download_selected_orders(self, request, orders):
        # Используем StringIO для работы с текстовыми данными в памяти
        output = io.StringIO()
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Записываем заголовки столбцов в CSV файл
        writer.writerow([header for header in self.CSV_COLUMNS.values()])

        # Записываем данные в CSV файл
        for order in orders:
            row_values = self.get_row_values(order)
            writer.writerow([row_values.get(column, "") for column in self.CSV_COLUMNS])

        # Преобразуем содержимое StringIO в байты с кодировкой utf-8
        response = HttpResponse(output.getvalue().encode('utf-8-sig'), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename={self.get_download_filename(request)}'
        output.close()

        return response

    def change_order_statuses(self, request, orders):
        for order in orders:
            self.change_order_status(request, order)
        return redirect("dashboard:order-list")

    def change_order_status(self, request, order):
        # This method is pretty similar to what
        # OrderDetailView.change_order_status does. Ripe for refactoring.
        new_status = request.POST["new_status"].strip()
        if not new_status:
            messages.error(request, "Новый статус '%s' не действительный" % new_status)
        elif new_status not in order.available_statuses():
            messages.error(
                request,
                "Новый статус '%s' недействительно для этого заказа" % new_status,
            )
        else:
            handler = self.get_handler(user=request.user)
            old_status = order.status
            try:
                handler.handle_order_status_change(order, new_status)
            except PaymentError as e:
                messages.error(
                    request,
                    "Невозможно изменить статус заказа из-за ошибки оплаты.: %s" % e,
                )
            else:
                msg = (
                    "Статус заказа №%(number)s изменился с '%(old_status)s' на '%(new_status)s'"
                ) % {"old_status": old_status, "new_status": new_status, "number": order.number}
                messages.info(request, msg)


class OrderActiveListView(OrderListView):
    template_name = "oscar/dashboard/orders/active_order_list.html"
    form_class = ActiveOrderSearchForm
    
    def get_queryset(self):
        """
        Build the queryset for this list.
        """
        active_statuses = settings.ORDER_ACTIVE_STATUSES
        queryset = sort_queryset(
            self.base_queryset, self.request, ["number", "total"]
        ).filter(status__in=active_statuses).order_by(
            "order_time"
        )

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data.get("store", None):
            queryset = queryset.filter(
                store__code=data["store"]
        )

        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        ctx["order_statuses"] = Order.all_statuses()
        ctx["title"] = "Активные заказы"
        return ctx

    def change_order_statuses(self, request, orders):
        for order in orders:
            self.change_order_status(request, order)
        return redirect("dashboard:order-active-list")


class OrderActiveListLookupView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    table_class = OrderTable
    form_class = ActiveOrderSearchForm
    template_name = "oscar/dashboard/table.html"

    def get(self, request):
        """
        Build the queryset for this list.
        """
        user = request.user
        active_statuses = settings.ORDER_ACTIVE_STATUSES
        self.form = self.form_class(request.GET)

        if not self.form.is_valid():
            return JsonResponse({'update': False})
        
        # Построение базового queryset с фильтрацией
        queryset = queryset_orders(user=user).filter(status__in=active_statuses)

        # Применяем фильтрацию по store только если store существует
        store_code = self.form.cleaned_data.get("store")
        if store_code:
            queryset = queryset.filter(store__code=store_code)

        num_orders = queryset.count()

        # Проверяем, требует ли запрос обновления
        if num_orders <= int(request.GET.get('order_num', 0)) and request.GET.get('force', 'false') == 'false':
            return JsonResponse({'update': False, 'num_orders': num_orders})
        
        # Аннотируем и сортируем queryset
        queryset = (
            queryset.order_by("order_time")
            .annotate(
                source=Max("sources__reference"),
                amount_paid=Sum("sources__amount_debited") - Sum("sources__amount_refunded"),
                paid=F("sources__paid"),
                before_order=Case(
                    When(date_finish__isnull=True, then=ExpressionWrapper(F('order_time') - now(), output_field=DurationField())),
                    default=Value(None),
                    output_field=DurationField(),
                ),
            )
        )

        # Сортировка в зависимости от запроса
        queryset = sort_queryset(queryset, request, ["number", "total"])

        # Формируем таблицу и рендерим HTML
        table = self.table_class(queryset)
        RequestConfig(request).configure(table)
        html = render(request, self.template_name, {'table': table}).content.decode('utf-8')

        return JsonResponse({'html': html, 'update': True, 'num_orders': num_orders})


class OrderModalView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get(self, request, *args, **kwargs):
        order_number = request.GET.get('order_number', None)
        try:
            order = Order.objects.get(number=order_number)
            order.open()
            if not order.date_finish:
                order.before_order = order.order_time - now()
            else:
                order.before_order = None
            lines = order.lines.all()
            order_paid = 0
            for src in order.sources.all():
                order_paid += src.amount_debited - src.amount_refunded

            order_html = render_to_string("oscar/dashboard/orders/partials/order-modal.html", {"order": order, "order_paid": order_paid, "lines": lines}, request=self.request)
            return JsonResponse({"html": order_html}, status = 200)
        except Exception:
            return JsonResponse({'order': None})
        

class OrderNextStatusView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def post(self, request, *args, **kwargs):
        order_number = request.data.get('order_number', None)
        try:
            order = Order.objects.get(number=order_number)
            next_status = request.data.get('next_status', order.status)
            order.set_status(next_status)
            if next_status in settings.ORDER_FINAL_STATUSES:
                return JsonResponse({"next_status": None, "final": True}, status = 200)
            return JsonResponse({"next_status": order.next_status, "final": False}, status = 200)
        except Exception:
            JsonResponse({"next_status": None}, status = 400)
        

class OrderDetailView(EventHandlerMixin, DetailView):
    """
    Dashboard view to display a single order.

    Supports the permission-based dashboard.
    """

    model = Order
    context_object_name = "order"
    template_name = "oscar/dashboard/orders/order_detail.html"

    # These strings are method names that are allowed to be called from a
    # submitted form.
    order_actions = (
        "save_note",
        "delete_note",
        "change_order_status",
        "create_order_payment_event",
    )
    line_actions = (
        "change_line_statuses",
        "create_shipping_event",
        "create_payment_event",
    )

    def get_object(self, queryset=None):
        order = get_order_or_404(self.request.user, self.kwargs["number"])
        order.open()
        if not order.date_finish:
            order.before_order = order.order_time - now()
            # order.before_order = relativedelta(order.order_time, now())
        else:
            order.before_order = None
        return order

    def get_order_lines(self):
        return self.object.lines.all()

    def post(self, request, *args, **kwargs):
        # For POST requests, we use a dynamic dispatch technique where a
        # parameter specifies what we're trying to do with the form submission.
        # We distinguish between order-level actions and line-level actions.

        order = self.object = self.get_object()

        # Look for order-level action first
        if "order_action" in request.POST:
            return self.handle_order_action(
                request, order, request.POST["order_action"]
            )

        # Look for line-level action
        if "line_action" in request.POST:
            return self.handle_line_action(request, order, request.POST["line_action"])

        return self.reload_page(error="Корректные действия не отправлены")

    def handle_order_action(self, request, order, action):
        if action not in self.order_actions:
            return self.reload_page(error="Недопустимое действие")
        return getattr(self, action)(request, order)

    def handle_line_action(self, request, order, action):
        if action not in self.line_actions:
            return self.reload_page(error="Недопустимое действие")

        # Load requested lines
        line_ids = request.POST.getlist("selected_line")
        if len(line_ids) == 0:
            return self.reload_page(error="Вы должны выбрать несколько строк для действий.")

        lines = self.get_order_lines()
        lines = lines.filter(id__in=line_ids)
        if len(line_ids) != len(lines):
            return self.reload_page(error="Запрошены неверные строки")

        # Build list of line quantities
        line_quantities = []
        for line in lines:
            qty = request.POST.get("selected_line_qty_%s" % line.id)
            try:
                qty = int(qty)
            except ValueError:
                qty = None
            if qty is None or qty <= 0:
                error_msg = ("Введенное количество для строки #%s не действует")
                return self.reload_page(error=error_msg % line.id)
            elif qty > line.quantity:
                error_msg = (
                    "Введенное количество для строки #%(line_id)s "
                    "не должно быть выше, чем %(quantity)s"
                )
                kwargs = {"line_id": line.id, "quantity": line.quantity}
                return self.reload_page(error=error_msg % kwargs)

            line_quantities.append(qty)

        return getattr(self, action)(request, order, lines, line_quantities)

    def reload_page(self, fragment=None, error=None):
        url = reverse("dashboard:order-detail", kwargs={"number": self.object.number})
        if fragment:
            url += "#" + fragment
        if error:
            messages.error(self.request, error)
        return HttpResponseRedirect(url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_tab"] = kwargs.get("active_tab", "lines")

        # Forms
        ctx["note_form"] = self.get_order_note_form()
        ctx["order_status_form"] = self.get_order_status_form()

        ctx["lines"] = self.get_order_lines()
        ctx["line_statuses"] = Line.all_statuses()
        ctx["shipping_event_types"] = ShippingEventType.objects.all()
        ctx["payment_event_types"] = PaymentEventType.objects.all()
        
        user_orders = Order.objects.filter(user=ctx['order'].user)
        order_amount = 0
        for order in user_orders:
            order_amount += order.total

        ctx["user_info"] = {
            "order_count": user_orders.count(),
            "order_amount": order_amount,
        }

        paid = 0
        for src in ctx['order'].sources.all():
            paid += src.amount_debited - src.amount_refunded

        ctx["order_paid"] = paid

        transactions = self.get_payment_transactions()
        ctx["payment_transactions"] = transactions

        transactions_source_id = []
        for trans in transactions:
            transactions_source_id.append(trans.source_id)
        ctx["payment_transactions_source_id"] = transactions_source_id

        return ctx

    # Data fetching methods for template context

    def get_payment_transactions(self):
        # return Transaction.objects.filter(source__order=self.object)
        transactions = Transaction.objects.filter(source__order=self.object)
        for trans in transactions:
            setattr(trans, 'source_refundable', trans.source.refundable)
        return transactions
    
    def get_order_note_form(self):
        kwargs = {"order": self.object, "user": self.request.user, "data": None}
        if self.request.method == "POST":
            kwargs["data"] = self.request.POST
        note_id = self.kwargs.get("note_id", None)
        if note_id:
            note = get_object_or_404(OrderNote, order=self.object, id=note_id)
            if note.is_editable():
                kwargs["instance"] = note
        return OrderNoteForm(**kwargs)

    def get_order_status_form(self):
        data = None
        if self.request.method == "POST":
            data = self.request.POST
        return OrderStatusForm(order=self.object, data=data)

    # Order-level actions

    # pylint: disable=unused-argument
    def save_note(self, request, order):
        form = self.get_order_note_form()
        if form.is_valid():
            form.save()
            messages.success(self.request, "Заметка сохранена")
            return self.reload_page(fragment="notes")

        ctx = self.get_context_data(note_form=form, active_tab="notes")
        return self.render_to_response(ctx)

    def delete_note(self, request, order):
        try:
            note = order.notes.get(id=request.POST.get("note_id", None))
        except ObjectDoesNotExist:
            messages.error(request, "Примечание не может быть удалено")
        else:
            messages.info(request, "Примечание удалено")
            note.delete()
        return self.reload_page()

    def change_order_status(self, request, order):
        form = self.get_order_status_form()
        if not form.is_valid():
            return self.reload_page(error="Неверная отправка формы")

        old_status, new_status = order.status, form.cleaned_data["new_status"]
        handler = self.get_handler(user=request.user)

        success_msg = (
            "Статус заказа изменился с '%(old_status)s' на '%(new_status)s'"
        ) % {"old_status": old_status, "new_status": new_status}
        try:
            handler.handle_order_status_change(order, new_status, note_msg=success_msg)
        except PaymentError as e:
            messages.error(
                request,
                ("Невозможно изменить статус заказа из-за ошибки оплаты.: %s") % e,
            )
        except order_exceptions.InvalidOrderStatus:
            # The form should validate against this, so we should only end up
            # here during race conditions.
            messages.error(
                request, "Невозможно изменить статус заказа в соответствии с запрошенным - новый статус недействителен"
            )
        else:
            messages.info(request, success_msg)
        return self.reload_page()

    def create_order_payment_event(self, request, order):
        """
        Create a payment event for the whole order
        """
        amount_str = request.POST.get("amount", None)
        try:
            amount = D(amount_str)
        except InvalidOperation:
            messages.error(request, "Пожалуйста, выберите действительную сумму")
            return self.reload_page()
        return self._create_payment_event(request, order, amount)

    # Line-level actions

    # pylint: disable=unused-argument
    def change_line_statuses(self, request, order, lines, quantities):
        new_status = request.POST["new_status"].strip()
        if not new_status:
            messages.error(request, "Новый статус '%s' не действует" % new_status)
            return self.reload_page()
        errors = []
        for line in lines:
            if new_status not in line.available_statuses():
                errors.append(
                    ("'%(status)s' недопустимый новый статус для позиции %(line_id)d")
                    % {"status": new_status, "line_id": line.id}
                )
        if errors:
            messages.error(request, "\n".join(errors))
            return self.reload_page()

        msgs = []
        for line in lines:
            msg = (
                "Статус позиции #%(line_id)d изменен с '%(old_status)s'"
                " на '%(new_status)s'"
            ) % {
                "line_id": line.id,
                "old_status": line.status,
                "new_status": new_status,
            }
            msgs.append(msg)
            line.set_status(new_status)
        message = "\n".join(msgs)
        messages.info(request, message)
        order.notes.create(
            user=request.user, message=message, note_type=OrderNote.SYSTEM
        )
        return self.reload_page()

    def create_shipping_event(self, request, order, lines, quantities):
        code = request.POST["shipping_event_type"]
        try:
            event_type = ShippingEventType._default_manager.get(code=code)
        except ShippingEventType.DoesNotExist:
            messages.error(request, "Тип события '%s' не действительный" % code)
            return self.reload_page()

        reference = request.POST.get("reference", None)
        try:
            self.get_handler().handle_shipping_event(
                order, event_type, lines, quantities, reference=reference
            )
        except order_exceptions.InvalidShippingEvent as e:
            messages.error(request, "Не удалось создать событие доставки.: %s" % e)
        except order_exceptions.InvalidStatus as e:
            messages.error(request, "Не удалось создать событие доставки.: %s" % e)
        except PaymentError as e:
            messages.error(
                request, "Невозможно создать событие доставки из-за ошибки платежа.: %s" % e,
            )
        else:
            messages.success(request, "Событие доставки создано")
        return self.reload_page()

    def create_payment_event(self, request, order, lines, quantities):
        """
        Create a payment event for a subset of order lines
        """
        amount_str = request.POST.get("amount", None)

        # If no amount passed, then we add up the total of the selected lines
        if not amount_str:
            amount = sum([line.line_price for line in lines])
        else:
            try:
                amount = D(amount_str)
            except InvalidOperation:
                messages.error(request, "Пожалуйста, выберите корректную сумму")
                return self.reload_page()

        return self._create_payment_event(request, order, amount, lines, quantities)

    def _create_payment_event(
        self, request, order, amount, lines=None, quantities=None
    ):
        code = request.POST.get("payment_event_type")
        try:
            event_type = PaymentEventType._default_manager.get(code=code)
        except PaymentEventType.DoesNotExist:
            messages.error(request, "Тип события '%s' не действительный" % code)
            return self.reload_page()
        try:
            self.get_handler().handle_payment_event(
                order, event_type, amount, lines, quantities
            )
        except PaymentError as e:
            messages.error(
                request, "Невозможно создать платежное событие из-за ошибки платежа: %s" % e
                )
        except order_exceptions.InvalidPaymentEvent as e:
            messages.error(request, "Невозможно создать событие платежа: %s" % e)
        else:
            messages.info(request, "Событие платежа создано")
        return self.reload_page()


class LineDetailView(DetailView):
    """
    Dashboard view to show a single line of an order.
    Supports the permission-based dashboard.
    """

    model = Line
    context_object_name = "line"
    template_name = "oscar/dashboard/orders/line_detail.html"

    def get_object(self, queryset=None):
        order = get_order_or_404(self.request.user, self.kwargs["number"])
        try:
            return order.lines.get(pk=self.kwargs["line_id"])
        except self.model.DoesNotExist:
            raise Http404()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["order"] = self.object.order
        return ctx


def get_changes_between_models(model1, model2, excludes=None):
    """
    Return a dict of differences between two model instances
    """
    if excludes is None:
        excludes = []
    changes = {}
    for field in model1._meta.fields:
        if (
            isinstance(field, (fields.AutoField, fields.related.RelatedField))
            or field.name in excludes
        ):
            continue

        if field.value_from_object(model1) != field.value_from_object(model2):
            changes[field.verbose_name] = (
                field.value_from_object(model1),
                field.value_from_object(model2),
            )
    return changes

def get_change_summary(model1, model2):
    """
    Generate a summary of the changes between two address models
    """
    changes = get_changes_between_models(model1, model2, ["search_text"])
    change_descriptions = []
    for field, delta in changes.items():
        change_descriptions.append(
            ("%(field)s изменено с '%(old_value)s' на '%(new_value)s'")
            % {"field": field, "old_value": delta[0], "new_value": delta[1]}
        )
    return "\n".join(change_descriptions)


class ShippingAddressUpdateView(UpdateView):
    """
    Dashboard view to update an order's shipping address.
    Supports the permission-based dashboard.
    """

    model = ShippingAddress
    context_object_name = "address"
    template_name = "oscar/dashboard/orders/shippingaddress_form.html"
    form_class = ShippingAddressForm

    def get_object(self, queryset=None):
        order = get_order_or_404(self.request.user, self.kwargs["number"])
        return get_object_or_404(self.model, order=order)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["order"] = self.object.order
        return ctx

    def form_valid(self, form):
        old_address = ShippingAddress.objects.get(id=self.object.id)
        response = super().form_valid(form)
        changes = get_change_summary(old_address, self.object)
        if changes:
            msg = "Адрес доставки обновлен:\n%s" % changes
            self.object.order.notes.create(
                user=self.request.user, message=msg, note_type=OrderNote.SYSTEM
            )
        return response

    def get_success_url(self):
        messages.info(self.request, "Адрес доставки обновлен")
        return reverse(
            "dashboard:order-detail",
            kwargs={
                "number": self.object.order.number,
            },
        )
