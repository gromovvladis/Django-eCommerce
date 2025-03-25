from io import TextIOWrapper

from core.loading import get_class, get_classes, get_model
from core.views.generic import BulkEditMixin
from django.conf import settings
from django.contrib import messages
from django.core import exceptions
from django.db.models import Count
from django.shortcuts import HttpResponse, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import ngettext
from django.views.generic import (CreateView, DeleteView, ListView, UpdateView,
                                  View)
from django_tables2 import SingleTableView

RangeTable = get_class("dashboard.ranges.tables", "RangeTable")
RangeForm, RangeProductForm = get_classes(
    "dashboard.ranges.forms", ["RangeForm", "RangeProductForm"]
)

Range = get_model("offer", "Range")
RangeProduct = get_model("offer", "RangeProduct")
RangeProductFileUpload = get_model("offer", "RangeProductFileUpload")
Product = get_model("catalogue", "Product")


class RangeListView(SingleTableView):
    template_name = "dashboard/ranges/range_list.html"
    table_class = RangeTable
    context_table_name = "ranges"
    paginate_by = settings.DASHBOARD_ITEMS_PER_PAGE

    def get_queryset(self):
        return Range._default_manager.prefetch_related(
            "included_categories", "included_products"
        ).annotate(
            benefits=Count("benefit"),
            included_categories_count=Count("included_categories"),
        )


class RangeCreateView(CreateView):
    model = Range
    template_name = "dashboard/ranges/range_form.html"
    form_class = RangeForm

    def get_success_url(self):
        if "action" in self.request.POST:
            return reverse("dashboard:range-products", kwargs={"pk": self.object.id})
        else:
            msg = render_to_string(
                "dashboard/ranges/messages/range_saved.html",
                {"range": self.object},
            )
            messages.success(self.request, msg, extra_tags="safe noicon")
            return reverse("dashboard:range-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Создать диапазон"
        return ctx


class RangeUpdateView(UpdateView):
    model = Range
    template_name = "dashboard/ranges/range_form.html"
    form_class = RangeForm

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_editable:
            raise exceptions.PermissionDenied("Not allowed")
        return obj

    def get_success_url(self):
        if "action" in self.request.POST:
            return reverse("dashboard:range-products", kwargs={"pk": self.object.id})
        else:
            msg = render_to_string(
                "dashboard/ranges/messages/range_saved.html",
                {"range": self.object},
            )
            messages.success(self.request, msg, extra_tags="safe noicon")
            return reverse("dashboard:range-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["range"] = self.object
        ctx["title"] = self.object.name
        return ctx


class RangeDeleteView(DeleteView):
    model = Range
    template_name = "dashboard/ranges/range_delete.html"
    context_object_name = "range"

    def get_success_url(self):
        messages.warning(self.request, "Диапазон удален.")
        return reverse("dashboard:range-list")


class RangeProductListView(BulkEditMixin, ListView):
    model = Product
    template_name = "dashboard/ranges/range_product_list.html"
    context_object_name = "products"
    actions = (
        "add_products",
        "add_excluded_products",
        "remove_selected_products",
        "remove_excluded_products",
    )
    form_class = RangeProductForm
    paginate_by = settings.DASHBOARD_ITEMS_PER_PAGE

    # pylint: disable=attribute-defined-outside-init
    def get(self, request, *args, **kwargs):
        self.upload_type = request.GET.get("upload_type", "")
        return super().get(request, *args, **kwargs)

    # pylint: disable=attribute-defined-outside-init
    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        self.upload_type = request.POST.get("upload_type", "")
        if request.POST.get("action", None) == "add_products":
            return self.add_products(request)
        if request.POST.get("action", None) == "add_excluded_products":
            return self.add_excluded_products(request)
        if request.POST.get("action", None) == "remove_excluded_products":
            return self.remove_excluded_products(request)
        return super().post(request, *args, **kwargs)

    def get_product_range(self):
        if not hasattr(self, "_product_range"):
            self._product_range = get_object_or_404(Range, id=self.kwargs["pk"])
        return self._product_range

    def get_queryset(self):
        products = self.get_product_range().all_products()
        return products.order_by("rangeproduct__display_order")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product_range = self.get_product_range()
        ctx["range"] = product_range
        if "form" not in ctx:
            ctx["form"] = self.form_class(
                product_range,
                initial={"upload_type": RangeProductFileUpload.INCLUDED_PRODUCTS_TYPE},
            )
        if "form_excluded" not in ctx:
            ctx["form_excluded"] = self.form_class(
                product_range,
                initial={"upload_type": RangeProductFileUpload.EXCLUDED_PRODUCTS_TYPE},
            )
        ctx["file_uploads_included"] = product_range.file_uploads.filter(
            upload_type=RangeProductFileUpload.INCLUDED_PRODUCTS_TYPE
        )
        ctx["file_uploads_excluded"] = product_range.file_uploads.filter(
            upload_type=RangeProductFileUpload.EXCLUDED_PRODUCTS_TYPE
        )
        ctx["upload_type"] = self.upload_type
        return ctx

    def remove_selected_products(self, request, products):
        product_range = self.get_product_range()
        for product in products:
            product_range.remove_product(product)
        num_products = len(products)
        messages.success(
            request,
            ngettext(
                "Удален %d товар из ассортимента.",
                "Удалено %d товаров из ассортимента.",
                num_products,
            )
            % num_products,
        )
        return redirect(
            reverse("dashboard:range-products", kwargs={"pk": product_range.pk})
        )

    def add_products(self, request):
        product_range = self.get_product_range()
        form = self.form_class(product_range, request.POST, request.FILES)
        if not form.is_valid():
            ctx = self.get_context_data(form=form, object_list=self.object_list)
            return self.render_to_response(ctx)

        self.handle_query_products(request, product_range, form)
        self.handle_file_products(request, product_range, form)
        return redirect(
            reverse("dashboard:range-products", kwargs={"pk": product_range.pk})
        )

    def add_excluded_products(self, request):
        product_range = self.get_product_range()
        form = self.form_class(
            product_range,
            request.POST,
            request.FILES,
            initial={"upload_type": RangeProductFileUpload.EXCLUDED_PRODUCTS_TYPE},
        )
        if not form.is_valid():
            ctx = self.get_context_data(
                form_excluded=form, object_list=self.object_list
            )
            return self.render_to_response(ctx)

        self.handle_query_products(request, product_range, form)
        self.handle_file_products(request, product_range, form)
        return redirect(
            reverse("dashboard:range-products", kwargs={"pk": product_range.pk})
            + "?upload_type=excluded"
        )

    def remove_excluded_products(self, request):
        product_ids = request.POST.getlist("selected_product", None)
        products = self.model.objects.filter(id__in=product_ids)
        product_range = self.get_product_range()
        for product in products:
            product_range.excluded_products.remove(product)
        num_products = len(products)
        messages.success(
            request,
            ngettext(
                "Добавлен %d товар из исключенного списка.",
                "Добавлен %d товаров из исключенного списка.",
                num_products,
            )
            % num_products,
        )
        return redirect(
            reverse("dashboard:range-products", kwargs={"pk": product_range.pk})
            + "?upload_type=excluded"
        )

    def handle_query_products(self, request, product_range, form):
        products = form.get_products()
        if not products:
            return
        for product in products:
            if (
                form.cleaned_data["upload_type"]
                == RangeProductFileUpload.EXCLUDED_PRODUCTS_TYPE
            ):
                product_range.excluded_products.add(product)
                action = "исключено из этого диапазона"
            else:
                product_range.add_product(product)
                action = "добавлено в этот диапазон"
        num_products = len(products)
        messages.success(
            request,
            (
                "%(num_products)d товар был в %(action)s.",
                "%(num_products)d товаров было в %(action)s.",
                num_products,
            )
            % {"num_products": num_products, "action": action},
        )
        dupe_skus = form.get_duplicate_skus()
        if dupe_skus:
            messages.warning(
                request,
                "Товары с артикулами, соответствующими %(skus)s, уже были в %(action)s."
                % {"skus": ", ".join(dupe_skus), "action": action},
            )

        missing_skus = form.get_missing_skus()
        if missing_skus:
            messages.warning(
                request,
                "Не найдено ни одного товара(ов), соответствующего артикулу %s."
                % ", ".join(missing_skus),
            )
        self.check_imported_products_sku_duplicates(request, products)

    def handle_file_products(self, request, product_range, form):
        if "file_upload" not in request.FILES:
            return
        f = request.FILES["file_upload"]
        upload = self.create_upload_object(
            request, product_range, f, form.cleaned_data["upload_type"]
        )
        products = upload.process(TextIOWrapper(f, encoding=request.encoding))
        if not upload.was_processing_successful():
            messages.error(request, upload.error_message)
        else:
            if (
                form.cleaned_data["upload_type"]
                == RangeProductFileUpload.EXCLUDED_PRODUCTS_TYPE
            ):
                action = "excluded from this range"
            else:
                action = "added to this range"
            msg = render_to_string(
                "dashboard/ranges/messages/range_products_saved.html",
                {"range": product_range, "upload": upload, "action": action},
            )
            messages.success(request, msg, extra_tags="safe noicon block")
        self.check_imported_products_sku_duplicates(request, products)

    def create_upload_object(self, request, product_range, f, upload_type):
        upload = RangeProductFileUpload.objects.create(
            range=product_range,
            uploaded_by=request.user,
            filepath=f.name,
            size=f.size,
            upload_type=upload_type,
        )
        return upload

    def check_imported_products_sku_duplicates(self, request, queryset):
        dupe_sku_products = (
            queryset.values("stockrecords__evotor_code")
            .annotate(total=Count("stockrecords__evotor_code"))
            .filter(total__gt=1)
            .order_by("stockrecords__evotor_code")
        )
        if dupe_sku_products:
            dupe_skus = [p["stockrecords__evotor_code"] for p in dupe_sku_products]
            messages.warning(
                request,
                "Есть более одного товара с артикулом: %s." % ", ".join(dupe_skus),
            )


class RangeReorderView(View):
    # pylint: disable=unused-argument
    def post(self, request, pk):
        order = dict(request.POST).get("product")
        self._save_page_order(order)
        return HttpResponse(status=200)

    def _save_page_order(self, order):
        """
        Save the order of the products within range.
        """
        range_products = RangeProduct.objects.filter(
            range_id=self.kwargs["pk"], product_id__in=order
        )
        for range_product in range_products:
            range_product.display_order = order.index(str(range_product.product_id))
        RangeProduct.objects.bulk_update(range_products, ["display_order"])
