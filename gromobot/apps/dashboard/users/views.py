# pylint: disable=attribute-defined-outside-init
import re

from core.compat import get_user_model
from core.loading import get_class, get_classes, get_model
from core.views.generic import BulkEditMixin
from django.conf import settings
from django.contrib import messages
from django.db.models import (Case, Count, DurationField, ExpressionWrapper, F,
                              Max, Q, Sum, Value, When)
from django.shortcuts import redirect
from django.utils.timezone import now
from django.views.generic import DetailView
from django.views.generic.edit import FormMixin
from django_tables2 import MultiTableMixin, SingleTableView

UserSearchForm = get_class("dashboard.users.forms", "UserSearchForm")
UserTable = get_class("dashboard.users.tables", "UserTable")
OrderTable = get_class("dashboard.orders.tables", "OrderTable")
ReviewOrderTable, ReviewProductTable = get_classes(
    "dashboard.reviews.tables", ("ReviewOrderTable", "ReviewProductTable")
)

Order = get_model("order", "Order")
User = get_user_model()


class CustomerListView(BulkEditMixin, FormMixin, SingleTableView):
    template_name = "dashboard/users/customer_list.html"
    model = User
    actions = (
        "make_nothing",
        "make_active",
        "make_inactive",
    )
    form_class = UserSearchForm
    table_class = UserTable
    context_table_name = "users"
    desc_template = "%(main_filter)s %(phone_filter)s %(name_filter)s"
    description = ""

    def dispatch(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        self.form = self.get_form(form_class)
        return super().dispatch(request, *args, **kwargs)

    def get_table_pagination(self, table):
        return dict(per_page=settings.DASHBOARD_ITEMS_PER_PAGE)

    def get_form_kwargs(self):
        """
        Only bind search form if it was submitted.
        """
        kwargs = super().get_form_kwargs()

        if "search" in self.request.GET:
            kwargs.update(
                {
                    "data": self.request.GET,
                }
            )

        return kwargs

    def get_queryset(self):
        self.search_filters = []
        queryset = self.model.objects.select_related("userrecord").order_by(
            "-date_joined"
        )
        return self.apply_search(queryset)

    def apply_search(self, queryset):
        # Set initial queryset description, used for template context
        self.desc_ctx = {
            "main_filter": "Все пользователи",
            "phone_filter": "",
            "name_filter": "",
        }
        if self.form.is_valid():
            return self.apply_search_filters(queryset, self.form.cleaned_data)
        else:
            return queryset

    def apply_search_filters(self, queryset, data):
        """
        Function is split out to allow customisation with little boilerplate.
        """
        if data["username"]:
            username = re.sub(r"[^\d+]", "", data["username"])
            queryset = queryset.filter(username__istartswith=username)
            self.desc_ctx["phone_filter"] = (
                " с телефоном соответствующим '%s'" % username
            )
            self.search_filters.append(
                (
                    ('Телефон начинается с "%s"' % username),
                    (("username", data["username"]),),
                )
            )
        if data["name"]:
            # If the value is two words, then assume they are first name and
            # last name
            parts = data["name"].split()
            # always true filter
            condition = Q()
            for part in parts:
                condition &= Q(name__icontains=part)
            queryset = queryset.filter(condition).distinct()
            self.desc_ctx["name_filter"] = (
                " с именем соответствующим '%s'" % data["name"]
            )
            self.search_filters.append(
                (('Имя соответствует "%s"' % data["name"]), (("name", data["name"]),))
            )

        return queryset

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.caption = self.desc_template % self.desc_ctx
        return table

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["search_filters"] = self.search_filters
        return context

    def make_nothing(self, request, users):
        messages.info(self.request, "Выберите статус 'Активен' или 'Не активен'.")
        return redirect("dashboard:customer-list")

    def make_inactive(self, request, users):
        return self._change_users_active_status(users, False)

    def make_active(self, request, users):
        return self._change_users_active_status(users, True)

    def _change_users_active_status(self, users, value):
        for user in users:
            if not user.is_superuser:
                user.is_active = value
                user.save()
        messages.info(self.request, "Пользовательский статус был успешно изменен.")
        return redirect("dashboard:customer-list")


class UserDetailView(MultiTableMixin, DetailView):
    template_name = "dashboard/users/detail.html"
    model = User
    context_table_name = "tables"
    table_prefix = "customer_{}-"
    context_object_name = "customer"

    orders_table = OrderTable
    product_review_table = ReviewProductTable
    order_review_table = ReviewOrderTable

    def get_queryset(self):
        self.queryset = self.model.objects.prefetch_related(
            "orders__lines",
            "orders__surcharges",
            "orders__sources",
            "order_reviews",
            "product_reviews",
        ).annotate(
            total_reviews=Count("order_reviews", distinct=True)
            + Count("product_reviews", distinct=True),
        )
        return self.queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_orders = Order.objects.filter(user=context["customer"])
        order_amount = 0

        for order in user_orders:
            order_amount += order.total

        context["user_info"] = {
            "order_count": user_orders.count(),
            "order_amount": order_amount,
        }

        context["active_tab"] = "user_orders"

        return context

    def get_tables(self):
        self.user = self.queryset.get(pk=self.kwargs.get(self.pk_url_kwarg))
        return [
            self.get_orders_table(),
            self.get_order_reviews_table(),
            self.get_product_reviews_table(),
        ]

    def get_table_pagination(self, table):
        return dict(per_page=settings.EVOTOR_ITEMS_PER_PAGE)

    def get_orders_table(self):
        orders = self.user.orders.annotate(
            source=Max("sources__reference"),
            amount_paid=Sum("sources__amount_debited")
            - Sum("sources__amount_refunded"),
            before_order=Case(
                When(
                    date_finish__isnull=True,
                    then=ExpressionWrapper(
                        F("order_time") - now(), output_field=DurationField()
                    ),
                ),
                default=Value(None),
                output_field=DurationField(),
            ),
        )
        return self.orders_table(orders)

    def get_order_reviews_table(self):
        order_reviews = self.user.order_reviews.all()
        return self.order_review_table(order_reviews)

    def get_product_reviews_table(self):
        product_reviews = self.user.product_reviews.all()
        return self.product_review_table(product_reviews)
