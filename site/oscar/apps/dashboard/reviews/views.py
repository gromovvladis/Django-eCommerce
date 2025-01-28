# pylint: disable=attribute-defined-outside-init
import datetime

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import generic
from django_tables2 import SingleTableView

from oscar.core.loading import get_classes, get_model
from oscar.core.utils import format_datetime
from oscar.views import sort_queryset
from oscar.views.generic import BulkEditMixin

ProductReviewSearchForm, DashboardProductReviewForm, DashboardOrderReviewForm = get_classes(
    "dashboard.reviews.forms", ("ProductReviewSearchForm", "DashboardProductReviewForm", "DashboardOrderReviewForm")
)
ProductReview = get_model("reviews", "productreview")
OrderReview = get_model("customer", "OrderReview")

ReviewOrderTable, ReviewProductTable = get_classes(
    "dashboard.reviews.tables", ("ReviewOrderTable", "ReviewProductTable")
)

class BaseReviewListView(BulkEditMixin, SingleTableView):
    form_class = ProductReviewSearchForm
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    actions = ("update_selected_review_status",)
    context_table_name = "reviews"
    desc_template = (
        "%(main_filter)s %(date_filter)s %(status_filter)s"
        "%(kw_filter)s %(phone_filter)s"
    )

    def get(self, request, *args, **kwargs):
        response = super().get(request, **kwargs)
        self.form = self.form_class()
        return response

    def get_date_from_to_queryset(self, date_from, date_to, queryset=None):
        """
        Get a ``QuerySet`` of ``ProductReview`` items that match the time
        frame specified by *date_from* and *date_to*. Both parameters are
        expected to be in ``datetime`` format with *date_from* < *date_to*.
        If *queryset* is specified, it will be filtered according to the
        given dates. Otherwise, a new queryset for all ``ProductReview``
        items is created.
        """
        if queryset is None:
            queryset = self.model.objects.all()

        if date_from:
            queryset = queryset.filter(date_created__gte=date_from)
            self.desc_ctx["date_filter"] = " создан после %s" % format_datetime(
                date_from
            )
        if date_to:
            # Add 24 hours to make search inclusive
            date_to = date_to + datetime.timedelta(days=1)
            queryset = queryset.filter(date_created__lt=date_to)
            self.desc_ctx["date_filter"] = " созданный ранее %s" % format_datetime(
                date_to
            )

        if date_from and date_to:
            # override description
            self.desc_ctx["date_filter"] = (
                " создано между %(start_date)s и %(end_date)s"
            ) % {
                "start_date": format_datetime(date_from),
                "end_date": format_datetime(date_to),
            }
        return queryset

    def get_queryset(self):
        queryset = self._get_queryset()
        queryset = sort_queryset(
            queryset,
            self.request,
            ["date_created", "score"],
            default="-date_created",
        )
        self.desc_ctx = {
            "main_filter": "Все отзывы",
            "date_filter": "",
            "status_filter": "",
            "kw_filter": "",
            "phone_filter": "",
        }

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        queryset = self.add_filter_status(queryset, data["status"])
        queryset = self.add_filter_keyword(queryset, data["keyword"])
        queryset = self.add_filter_phone(queryset, data["username"])

        queryset = self.get_date_from_to_queryset(
            data["date_from"], data["date_to"], queryset
        )

        return queryset

    def add_filter_status(self, queryset, status):
        # checking for empty string rather then True is required
        # as zero is a valid value for 'status' but would be
        # evaluated to False
        if status != "":
            queryset = queryset.filter(status=status).distinct()
            display_status = self.form.get_friendly_status()
            self.desc_ctx["status_filter"] = (
                " со статусом соответствующим '%s'" % display_status
            )
        return queryset

    def add_filter_keyword(self, queryset, keyword):
        if keyword:
            queryset = queryset.filter(
                Q(product__name__icontains=keyword) | Q(body__icontains=keyword)
            ).distinct()
            self.desc_ctx["kw_filter"] = (
                " с ключевым словом соответствующим '%s'" % keyword
            )
        return queryset

    def add_filter_phone(self, queryset, phone):
        if phone:
            queryset.filter(user__username__istartswith=phone).distinct()
            # If the value is two words, then assume they are first name and
            # last name
            self.desc_ctx["phone_filter"] = " - найден пользователь '%s'" % phone

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["review_form"] = self.review_form_class()
        context["form"] = self.form
        context["description"] = self.desc_template % self.desc_ctx
        return context

    def update_selected_review_status(self, request, reviews):
        """
        Update the status of the selected *reviews* with the new
        status in the *request* POST data. Redirects back to the
        list view of reviews.
        """
        new_status = int(request.POST.get("status"))
        for review in reviews:
            review.status = new_status
            review.save()
        return HttpResponseRedirect(self.success_url)


class ReviewProductListView(BaseReviewListView):
    table_class = ReviewProductTable
    model = ProductReview
    review_form_class = DashboardProductReviewForm
    success_url = reverse_lazy("dashboard:reviews-product-list")
    template_name = "oscar/dashboard/reviews/review_list_product.html"

    def _get_queryset(self):
        return self.model.objects.select_related("product", "user").all()


class ReviewOrderListView(BaseReviewListView):
    table_class = ReviewOrderTable
    model = OrderReview
    review_form_class = DashboardOrderReviewForm
    success_url = reverse_lazy("dashboard:reviews-order-list")
    template_name = "oscar/dashboard/reviews/review_list_order.html"

    def _get_queryset(self):
        return self.model.objects.select_related("order", "user").all()


class ReviewProductUpdateView(generic.UpdateView):
    model = ProductReview
    template_name = "oscar/dashboard/reviews/review_update.html"
    form_class = DashboardProductReviewForm
    context_object_name = "review"

    def get_success_url(self):
        return reverse("dashboard:reviews-product-list")


class ReviewProductDeleteView(generic.DeleteView):
    model = ProductReview
    template_name = "oscar/dashboard/reviews/review_delete.html"
    context_object_name = "review"

    def get_success_url(self):
        return reverse("dashboard:reviews-product-list")


class ReviewOrderUpdateView(generic.UpdateView):
    model = OrderReview
    template_name = "oscar/dashboard/reviews/review_update.html"
    form_class = DashboardProductReviewForm
    context_object_name = "review"

    def get_success_url(self):
        return reverse("dashboard:reviews-order-list")


class ReviewOrderDeleteView(generic.DeleteView):
    model = OrderReview
    template_name = "oscar/dashboard/reviews/review_delete.html"
    context_object_name = "review"

    def get_success_url(self):
        return reverse("dashboard:reviews-order-list")
