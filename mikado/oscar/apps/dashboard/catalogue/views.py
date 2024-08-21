# pylint: disable=attribute-defined-outside-init
from typing import Any
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View, generic
from django_tables2 import SingleTableMixin, SingleTableView
from django.db.models import Count, Max, Min, Case, When, DecimalField, F
from django.utils.timezone import now

from oscar.core.loading import get_class, get_classes, get_model
from oscar.views.generic import ObjectLookupView

(
    ProductForm,
    ProductClassSelectForm,
    ProductSearchForm,
    ProductClassForm,
    CategoryForm,
    StockAlertSearchForm,
    AttributeOptionGroupForm,
    OptionForm,
    AdditionalForm
) = get_classes(
    "dashboard.catalogue.forms",
    (
        "ProductForm",
        "ProductClassSelectForm",
        "ProductSearchForm",
        "ProductClassForm",
        "CategoryForm",
        "StockAlertSearchForm",
        "AttributeOptionGroupForm",
        "OptionForm",
        "AdditionalForm",
    ),
)
(
    StockRecordFormSet,
    ProductCategoryFormSet,
    ProductImageFormSet,
    ProductRecommendationFormSet,
    ProductAdditionalFormSet,
    ProductClassAdditionalFormSet,
    ProductAttributesFormSet,
    AttributeOptionFormSet,
) = get_classes(
    "dashboard.catalogue.formsets",
    (
        "StockRecordFormSet",
        "ProductCategoryFormSet",
        "ProductImageFormSet",
        "ProductRecommendationFormSet",
        "ProductAdditionalFormSet",
        "ProductClassAdditionalFormSet",
        "ProductAttributesFormSet",
        "AttributeOptionFormSet",
    ),
)
ProductTable, ProductClassTable, CategoryTable, AttributeOptionGroupTable, OptionTable, AdditionalTable, StockAlertTable = get_classes(
    "dashboard.catalogue.tables",
    ("ProductTable", "ProductClassTable", "CategoryTable", "AttributeOptionGroupTable", "OptionTable", "AdditionalTable", "StockAlertTable"),
)
(PopUpWindowCreateMixin, PopUpWindowUpdateMixin, PopUpWindowDeleteMixin) = get_classes(
    "dashboard.views",
    ("PopUpWindowCreateMixin", "PopUpWindowUpdateMixin", "PopUpWindowDeleteMixin"),
)
PartnerProductFilterMixin = get_class(
    "dashboard.catalogue.mixins", "PartnerProductFilterMixin"
)
Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
ProductImage = get_model("catalogue", "ProductImage")
ProductCategory = get_model("catalogue", "ProductCategory")
ProductClass = get_model("catalogue", "ProductClass")
StockRecord = get_model("partner", "StockRecord")
StockAlert = get_model("partner", "StockAlert")
Partner = get_model("partner", "Partner")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
Option = get_model("catalogue", "Option")
Additional = get_model("catalogue", "Additional")


class ProductListView(PartnerProductFilterMixin, SingleTableView):
    """
    Dashboard view of the product list.
    Supports the permission-based dashboard.
    """

    template_name = "oscar/dashboard/catalogue/product_list.html"
    form_class = ProductSearchForm
    productclass_form_class = ProductClassSelectForm
    table_class = ProductTable
    context_table_name = "products"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        ctx["productclass_form"] = self.productclass_form_class()
        if self.request.GET:
            ctx["searching"] = True
        return ctx
    
    def get_table(self, **kwargs):
        if "recently_edited" in self.request.GET:
            kwargs.update(dict(orderable=False))

        table = super().get_table(**kwargs)

        if self.form.is_valid() and any(self.form.cleaned_data.values()):
            table.caption = "Результаты поиска: %s" % self.object_list.count()

        return table

    def get_table_pagination(self, table):
        return dict(per_page=settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE)

    def get_queryset(self):
        """
        Build the queryset for this list
        """
        queryset = Product.objects.browsable_dashboard().base_queryset().select_related()
        queryset = self.filter_queryset(queryset)
        queryset = self.apply_search(queryset)

        queryset = queryset.annotate(
            min_price=Case(
                When(structure="parent", then=Min("children__stockrecords__price")),
                default=Min('stockrecords__price'),
                output_field=DecimalField()
            ),
            max_price=Case(
                When(structure="parent", then=Max("children__stockrecords__price")),
                default=Max('stockrecords__price'),
                output_field=DecimalField()
            ),
            old_price=Case(
                When(structure="parent", then=Max("children__stockrecords__old_price")),
                default=Max('stockrecords__old_price'),
                output_field=DecimalField()
            ),
            variants=Count("children"),
        )

        return queryset

    def apply_search(self, queryset):
        """
        Search through the filtered queryset.

        We must make sure that we don't return search results that the user is not allowed
        to see (see filter_queryset).
        """
        self.form = self.form_class(self.request.GET)

        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        upc = data.get("upc")
        if upc:
            # Filter the queryset by upc
            # For usability reasons, we first look at exact matches and only return
            # them if there are any. Otherwise we return all results
            # that contain the UPC.

            # Look up all matches (child products, products not allowed to access) ...
            matches_upc = Product.objects.filter(
                Q(upc__iexact=upc) | Q(children__upc__iexact=upc)
            )

            # ... and use that to pick all standalone or parent products that the user is
            # allowed to access.
            qs_match = queryset.filter(
                Q(id__in=matches_upc.values("id"))
                | Q(id__in=matches_upc.values("parent_id"))
            )

            if qs_match.exists():
                # If there's a direct UPC match, return just that.
                queryset = qs_match
            else:
                # No direct UPC match. Let's try the same with an icontains search.
                matches_upc = Product.objects.filter(
                    Q(upc__icontains=upc) | Q(children__upc__icontains=upc)
                )
                queryset = queryset.filter(
                    Q(id__in=matches_upc.values("id"))
                    | Q(id__in=matches_upc.values("parent_id"))
                )

        title = data.get("title")        
        if title:
            queryset = queryset.filter(
                Q(title__icontains=title) | Q(children__title__icontains=title) | Q(variant__icontains=title)
            )
        
        categories = data.get("categories")
        if categories:
            queryset = queryset.filter(
                Q(categories__in=categories) | Q(children__categories__in=categories)
            )
        
        is_public = data.get("is_public")
        if is_public:
            queryset = queryset.filter(
                Q(is_public=is_public)
            )

        product_class = data.get("product_class")
        if product_class:
            queryset = queryset.filter(
                Q(product_class__in=product_class)
            )

        return queryset.distinct()


class ProductCreateRedirectView(generic.RedirectView):
    permanent = False
    productclass_form_class = ProductClassSelectForm

    def get_product_create_url(self, product_class):
        """Allow site to provide custom URL"""
        return reverse(
            "dashboard:catalogue-product-create",
            kwargs={"product_class_slug": product_class.slug},
        )

    def get_invalid_product_class_url(self):
        messages.error(self.request, "Пожалуйста, выберите тип продукта")
        return reverse("dashboard:catalogue-product-list")

    def get_redirect_url(self, *args, **kwargs):
        form = self.productclass_form_class(self.request.GET)
        if form.is_valid():
            product_class = form.cleaned_data["product_class"]
            return self.get_product_create_url(product_class)

        else:
            return self.get_invalid_product_class_url()


class ProductCreateUpdateView(PartnerProductFilterMixin, generic.UpdateView):
    """
    Dashboard view that is can both create and update products of all kinds.
    It can be used in three different ways, each of them with a unique URL
    pattern:
    - When creating a new standalone product, this view is called with the
      desired product class
    - When editing an existing product, this view is called with the product's
      primary key. If the product is a child product, the template considerably
      reduces the available form fields.
    - When creating a new child product, this view is called with the parent's
      primary key.

    Supports the permission-based dashboard.
    """

    template_name = "oscar/dashboard/catalogue/product_update.html"
    model = Product
    context_object_name = "product"

    form_class = ProductForm
    category_formset = ProductCategoryFormSet
    image_formset = ProductImageFormSet
    recommendations_formset = ProductRecommendationFormSet
    additional_formset = ProductAdditionalFormSet
    stockrecord_formset = StockRecordFormSet

    creating = False
    parent = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formsets = {
            "category_formset": self.category_formset,
            "image_formset": self.image_formset,
            "recommended_formset": self.recommendations_formset,
            "additional_formset": self.additional_formset,
            "stockrecord_formset": self.stockrecord_formset,
        }

    def dispatch(self, request, *args, **kwargs):
        resp = super().dispatch(request, *args, **kwargs)
        return self.check_objects_or_redirect() or resp

    def check_objects_or_redirect(self):
        """
        Allows checking the objects fetched by get_object and redirect
        if they don't satisfy our needs.
        Is used to redirect when create a new variant and the specified
        parent product can't actually be turned into a parent product.
        """
        if self.creating and self.parent is not None:
            is_valid, reason = self.parent.can_be_parent(give_reason=True)
            if not is_valid:
                messages.error(self.request, reason)
                return redirect("dashboard:catalogue-product-list")

    def get_queryset(self):
        """
        Filter products that the user doesn't have permission to update
        """
        return self.filter_queryset(Product.objects.all())

    def get_object(self, queryset=None):
        """
        This parts allows generic.UpdateView to handle creating products as
        well. The only distinction between an UpdateView and a CreateView
        is that self.object is None. We emulate this behavior.

        This method is also responsible for setting self.product_class and
        self.parent.
        """
        self.creating = "pk" not in self.kwargs
        if self.creating:
            # Specifying a parent product is only done when creating a child
            # product.
            parent_pk = self.kwargs.get("parent_pk")
            if parent_pk is None:
                self.parent = None
                # A product class needs to be specified when creating a
                # standalone product.
                product_class_slug = self.kwargs.get("product_class_slug")
                self.product_class = get_object_or_404(
                    ProductClass, slug=product_class_slug
                )
            else:
                self.parent = get_object_or_404(Product, pk=parent_pk)
                self.product_class = self.parent.product_class

            return None  # success
        else:
            product = super().get_object(queryset)
            self.product_class = product.get_product_class()
            self.parent = product.parent
            return product

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product_class"] = self.product_class
        ctx["class_additionals"] = self.product_class.class_additionals.all()
        ctx["parent"] = self.parent
        ctx["title"] = self.get_page_title()

        for ctx_name, formset_class in self.formsets.items():
            if ctx_name not in ctx:
                ctx[ctx_name] = formset_class(
                    self.product_class, self.request.user, instance=self.object
                )
        return ctx

    def get_page_title(self):
        if self.creating:
            if self.parent is None:
                return ("Создать новый %(product_class)s продукт") % {
                    "product_class": self.product_class.name
                }
            else:
                return ("Создать новый вариант продукта %(parent_product)s") % {
                    "parent_product": self.parent.title
                }
        else:
            if self.object.title or not self.parent:
                return self.object.title
            else:
                return ("Редактирование вариации товара - %(parent_product)s") % {
                    "parent_product": self.parent.title
                }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["product_class"] = self.product_class
        kwargs["parent"] = self.parent
        return kwargs

    def process_all_forms(self, form):
        """
        Short-circuits the regular logic to have one place to have our
        logic to check all forms
        """
        # Need to create the product here because the inline forms need it
        # can't use commit=False because ProductForm does not support it
        if self.creating and form.is_valid():
            self.object = form.save()

        formsets = {}
        for ctx_name, formset_class in self.formsets.items():
            formsets[ctx_name] = formset_class(
                self.product_class,
                self.request.user,
                self.request.POST,
                self.request.FILES,
                instance=self.object,
            )

        is_valid = form.is_valid() and all(
            [formset.is_valid() for formset in formsets.values()]
        )

        cross_form_validation_result = self.clean(form, formsets)
        if is_valid and cross_form_validation_result:
            return self.forms_valid(form, formsets)
        else:
            return self.forms_invalid(form, formsets)

    # form_valid and form_invalid are called depending on the validation result
    # of just the product form and redisplay the form respectively return a
    # redirect to the success URL. In both cases we need to check our formsets
    # as well, so both methods do the same. process_all_forms then calls
    # forms_valid or forms_invalid respectively, which do the redisplay or
    # redirect.
    form_valid = form_invalid = process_all_forms

    # pylint: disable=unused-argument
    def clean(self, form, formsets):
        """
        Perform any cross-form/formset validation. If there are errors, attach
        errors to a form or a form field so that they are displayed to the user
        and return False. If everything is valid, return True. This method will
        be called regardless of whether the individual forms are valid.
        """
        return True

    def forms_valid(self, form, formsets):
        """
        Save all changes and display a success url.
        When creating the first child product, this method also sets the new
        parent's structure accordingly.
        """
        if self.creating:
            self.handle_adding_child(self.parent)
        else:
            # a just created product was already saved in process_all_forms()
            self.object = form.save()
            self.update_alerts()

        # Save formsets
        for formset in formsets.values():
            formset.save()

        for idx, image in enumerate(self.object.images.all()):
            image.display_order = idx
            image.save()

        return HttpResponseRedirect(self.get_success_url())


    def update_alerts(self):
        # Извлекаем все StockRecord, где num_in_stock больше low_stock_threshold
        stock_records = StockRecord.objects.filter(product=self.object, num_in_stock__gt=F('low_stock_threshold'))

        # Проходим по найденным StockRecord и обновляем соответствующие StockAlert
        for stock_record in stock_records:
            # Находим все связанные с этим StockRecord уведомления
            stock_alerts = StockAlert.objects.filter(stockrecord=stock_record, status=StockAlert.OPEN)
            
            # Обновляем статус каждого найденного уведомления
            for alert in stock_alerts:
                alert.status = StockAlert.CLOSED
                alert.date_closed = now()
                alert.save()

    def handle_adding_child(self, parent):
        """
        When creating the first child product, the parent product needs
        to be implicitly converted from a standalone product to a
        parent product.
        """
        # ProductForm eagerly sets the future parent's structure to PARENT to
        # pass validation, but it's not persisted in the database. We ensure
        # it's persisted by calling save()
        if parent is not None:
            parent.structure = Product.PARENT
            parent.save()

    def forms_invalid(self, form, formsets):
        # delete the temporary product again
        if self.creating and self.object and self.object.pk is not None:
            self.object.delete()
            self.object = None

        messages.error(self.request, "Отправленные вами данные недействительны. Исправьте ошибки ниже.")
        ctx = self.get_context_data(form=form, **formsets)
        return self.render_to_response(ctx)

    def get_url_with_querystring(self, url):
        url_parts = [url]
        if self.request.GET.urlencode():
            url_parts += [self.request.GET.urlencode()]
        return "?".join(url_parts)

    def get_success_url(self):
        """
        Renders a success message and redirects depending on the button:
        - Standard case is pressing "Save"; redirects to the product list
        - When "Save and continue" is pressed, we stay on the same page
        - When "Create (another) child product" is pressed, it redirects
          to a new product creation page
        """
        msg = render_to_string(
            "oscar/dashboard/catalogue/messages/product_saved.html",
            {
                "product": self.object,
                "creating": self.creating,
                "request": self.request,
            },
        )
        messages.success(self.request, msg, extra_tags="safe noicon")

        action = self.request.POST.get("action")
        if action == "continue":
            url = reverse("dashboard:catalogue-product", kwargs={"pk": self.object.id})
        elif action == "create-another-child" and self.parent:
            url = reverse(
                "dashboard:catalogue-product-create-child",
                kwargs={"parent_pk": self.parent.pk},
            )
        elif action == "create-child":
            url = reverse(
                "dashboard:catalogue-product-create-child",
                kwargs={"parent_pk": self.object.pk},
            )
        else:
            url = reverse("dashboard:catalogue-product-list")
        return self.get_url_with_querystring(url)


class ProductDeleteView(PartnerProductFilterMixin, generic.DeleteView):
    """
    Dashboard view to delete a product. Has special logic for deleting the
    last child product.
    Supports the permission-based dashboard.
    """

    template_name = "oscar/dashboard/catalogue/product_delete.html"
    model = Product
    context_object_name = "product"

    def get_queryset(self):
        """
        Filter products that the user doesn't have permission to update
        """
        return self.filter_queryset(Product.objects.all())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object.is_child:
            ctx["title"] = "Удалить вариант продукта?"
        else:
            ctx["title"] = "Удалить продукт?"
        return ctx

    def delete(self, request, *args, **kwargs):
        # We override the core delete method and don't call super in order to
        # apply more sophisticated logic around handling child products.
        # Calling super makes it difficult to test if the product being deleted
        # is the last child.

        self.object = self.get_object()

        # Before performing the delete, record whether this product is the last
        # child.
        is_last_child = False
        if self.object.is_child:
            parent = self.object.parent
            is_last_child = parent.children.count() == 1

        # This also deletes any child products.
        self.object.delete()

        # If the product being deleted is the last child, then pass control
        # to a method than can adjust the parent itself.
        if is_last_child:
            self.handle_deleting_last_child(parent)

        return HttpResponseRedirect(self.get_success_url())

    def handle_deleting_last_child(self, parent):
        # If the last child product is deleted, this view defaults to turning
        # the parent product into a standalone product. While this is
        # appropriate for many scenarios, it is intentionally easily
        # overridable and not automatically done in e.g. a Product's delete()
        # method as it is more a UX helper than hard business logic.
        parent.structure = parent.STANDALONE
        parent.save()

    def get_success_url(self):
        """
        When deleting child products, this view redirects to editing the
        parent product. When deleting any other product, it redirects to the
        product list view.
        """
        if self.object.is_child:
            msg = "Удаленный вариант продукта '%s'" % self.object.get_title()
            messages.success(self.request, msg)
            return reverse(
                "dashboard:catalogue-product", kwargs={"pk": self.object.parent_id}
            )
        else:
            msg = "Удаленный продукт '%s'" % self.object.title
            messages.success(self.request, msg)
            return reverse("dashboard:catalogue-product-list")


class StockAlertListView(SingleTableView):
    template_name = "oscar/dashboard/catalogue/stockalert_list.html"
    table_class = StockAlertTable
    context_table_name = "alerts"
    paginate_by = settings.OSCAR_STOCK_ALERTS_PER_PAGE

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        return ctx
    
    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)

        if "status" in self.request.GET:
            self.form = StockAlertSearchForm(self.request.GET)
            if self.form.is_valid():
                status = self.form.cleaned_data["status"]
                table.caption = 'Уведомление со статусом "%s"' % status
        else:
            self.form = StockAlertSearchForm()

        return table

    def get_queryset(self):
        if "status" in self.request.GET:
            self.form = StockAlertSearchForm(self.request.GET)
            if self.form.is_valid():
                status = self.form.cleaned_data["status"]
                return StockAlert.objects.filter(status=status).select_related("stockrecord").annotate(
                name=F("stockrecord__product__title"),
                partner=F("stockrecord__partner__name"),
                threshold=F("stockrecord__low_stock_threshold"),
                num_in_stock=F("stockrecord__num_in_stock"),
            )       
        else:
            return StockAlert.objects.all().select_related("stockrecord").annotate(
                name=F("stockrecord__product__title"),
                partner=F("stockrecord__partner__name"),
                threshold=F("stockrecord__low_stock_threshold"),
                num_in_stock=F("stockrecord__num_in_stock"),
            )


class StockAlertUpdateView(View):
    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        # Извлекаем все StockRecord, где num_in_stock больше low_stock_threshold
        product_id = kwargs['pk']
        stock_records = StockRecord.objects.filter(product_id=product_id, num_in_stock__gt=F('low_stock_threshold'))

        # Проходим по найденным StockRecord и обновляем соответствующие StockAlert
        for stock_record in stock_records:
            # Находим все связанные с этим StockRecord уведомления
            stock_alerts = StockAlert.objects.filter(stockrecord=stock_record, status=StockAlert.OPEN)
            
            # Обновляем статус каждого найденного уведомления
            for alert in stock_alerts:
                alert.status = StockAlert.CLOSED
                alert.date_closed = now()
                alert.save()

        return redirect('dashboard:stock-alert-list')


    def form_valid(self, form):
        # Дополнительная логика перед сохранением
        if form.cleaned_data['status'] == StockAlert.CLOSED and not form.cleaned_data['date_closed']:
            form.instance.date_closed = now()  # Устанавливаем дату закрытия, если статус закрыт и дата не установлена
        return super().form_valid(form)


class CategoryListView(SingleTableView):
    template_name = "oscar/dashboard/catalogue/category_list.html"
    table_class = CategoryTable
    context_table_name = "categories"

    def get_queryset(self):
        return Category.get_root_nodes().annotate(num_products=Count('product'))

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["child_categories"] = Category.get_root_nodes()
        return ctx


class CategoryDetailListView(SingleTableMixin, generic.DetailView):
    template_name = "oscar/dashboard/catalogue/category_list.html"
    model = Category
    context_object_name = "category"
    table_class = CategoryTable
    context_table_name = "categories"

    def get_table_data(self):
        return self.object.get_children()

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["child_categories"] = self.object.get_children()
        ctx["ancestors"] = self.object.get_ancestors_and_self()
        return ctx


class CategoryListMixin(object):
    def get_success_url(self):
        parent = self.object.get_parent(update=True)
        if parent is None:
            return reverse("dashboard:catalogue-category-list")
        else:
            return reverse(
                "dashboard:catalogue-category-detail-list", args=(parent.pk,)
            )


class CategoryCreateView(CategoryListMixin, generic.CreateView):
    template_name = "oscar/dashboard/catalogue/category_form.html"
    model = Category
    form_class = CategoryForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Добавить новую категорию"
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Категория успешно создана")
        return super().get_success_url()

    def get_initial(self):
        # set child category if set in the URL kwargs
        initial = super().get_initial()
        if "parent" in self.kwargs:
            initial["_ref_node_id"] = self.kwargs["parent"]
        return initial


class CategoryUpdateView(CategoryListMixin, generic.UpdateView):
    template_name = "oscar/dashboard/catalogue/category_form.html"
    model = Category
    form_class = CategoryForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Обновить категорию '%s'" % self.object.name
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Категория успешно обновлена")
        action = self.request.POST.get("action")
        if action == "continue":
            return reverse(
                "dashboard:catalogue-category-update", kwargs={"pk": self.object.id}
            )
        return super().get_success_url()


class CategoryDeleteView(CategoryListMixin, generic.DeleteView):
    template_name = "oscar/dashboard/catalogue/category_delete.html"
    model = Category

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["parent"] = self.object.get_parent()
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Категория успешно удалена")
        return super().get_success_url()


class ProductLookupView(ObjectLookupView):
    model = Product

    def get_queryset(self):
        return self.model.objects.browsable().all()

    def lookup_filter(self, qs, term):
        return qs.filter(Q(title__icontains=term) | Q(parent__title__icontains=term))


class AdditionalLookupView(ObjectLookupView):
    model = Additional

    def get_queryset(self):
        return self.model.objects.browsable().all()

    def lookup_filter(self, qs, term):
        return qs.filter(name__icontains=term) 
    
    # def custom_filter(self, qs):
    #     class_addit = product_class.class_additionals.all()
    #     id_list = []
    #     for add in class_addit:
    #         id_list.append(add.id)

    #     return qs.filter(pk__notin=id_list)


class ProductClassCreateUpdateView(generic.UpdateView):
    template_name = "oscar/dashboard/catalogue/product_class_form.html"
    model = ProductClass
    form_class = ProductClassForm
    additional_class_formset = ProductClassAdditionalFormSet
    product_attributes_formset = ProductAttributesFormSet

    def process_all_forms(self, form):
        """
        This validates both the ProductClass form and the
        ProductClassAttributes formset at once
        making it possible to display all their errors at once.
        """
        # pylint: disable=no-member
        if self.creating and form.is_valid():
            # the object will be needed by the product_attributes_formset
            self.object = form.save(commit=False)

        additional_formset = self.additional_class_formset(
            self.request.POST, self.request.FILES, instance=self.object
        )

        attributes_formset = self.product_attributes_formset(
            self.request.POST, self.request.FILES, instance=self.object
        )

        is_valid = form.is_valid() and attributes_formset.is_valid() and additional_formset.is_valid()

        if is_valid:
            return self.forms_valid(form, attributes_formset, additional_formset)
        else:
            return self.forms_invalid(form, attributes_formset, additional_formset)

    def forms_valid(self, form, attributes_formset, additional_formset):
        form.save()
        attributes_formset.save()
        additional_formset.save()

        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, form, attributes_formset, additional_formset):
        messages.error(self.request, "Отправленные вами данные недействительны. Исправьте ошибки ниже.")
        ctx = self.get_context_data(form=form, attributes_formset=attributes_formset, additional_formset=additional_formset)
        return self.render_to_response(ctx)

    # form_valid and form_invalid are called depending on the validation result
    # of just the product class form, and return a redirect to the success URL
    # or redisplay the form, respectively. In both cases we need to check our
    # formsets as well, so both methods do the same. process_all_forms then
    # calls forms_valid or forms_invalid respectively, which do the redisplay
    # or redirect.
    form_valid = form_invalid = process_all_forms

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        if "attributes_formset" not in ctx:
            ctx["attributes_formset"] = self.product_attributes_formset(
                instance=self.object
            )

        if "additional_formset" not in ctx:
            ctx["additional_formset"] = self.additional_class_formset(
                instance=self.object
            )

        # pylint: disable=no-member
        ctx["title"] = self.get_title()

        return ctx


class ProductClassCreateView(ProductClassCreateUpdateView):
    creating = True

    def get_object(self, queryset=None):
        return None

    def get_title(self):
        return "Добавить новый тип продукта"

    def get_success_url(self):
        messages.info(self.request, "Тип продукта успешно создан")
        return reverse("dashboard:catalogue-class-list")


class ProductClassUpdateView(ProductClassCreateUpdateView):
    creating = False

    def get_title(self):
        return "Обновить тип продукта '%s'" % self.object.name

    def get_success_url(self):
        messages.info(self.request, "Тип продукта успешно обновлен.")
        return reverse("dashboard:catalogue-class-list")

    def get_object(self, queryset=None):
        product_class = get_object_or_404(ProductClass, pk=self.kwargs["pk"])
        return product_class

    
class ProductClassListView(SingleTableView):
    template_name = "oscar/dashboard/catalogue/product_class_list.html"
    table_class = ProductClassTable
    context_table_name = "classes"

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["title"] = "Типы продуктов"
        return ctx

    def get_queryset(self):
        """
        Build the queryset for this list
        """
        queryset = ProductClass.objects.prefetch_related("options", "class_additionals").all()
        queryset = queryset.annotate(
            num_products=Count("products"),
            num_additionals=Count('class_additionals'),
        )

        return queryset


class ProductClassDeleteView(generic.DeleteView):
    template_name = "oscar/dashboard/catalogue/product_class_delete.html"
    model = ProductClass

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["title"] = "Удалить тип продукта '%s'" % self.object.name
        product_count = self.object.products.count()

        if product_count > 0:
            ctx["disallow"] = True
            ctx["title"] = "Невозможно удалить '%s'" % self.object.name
            messages.error(self.request, "%i товаров по-прежнему относятся к этому типу" % product_count)
        return ctx

    def get_success_url(self):
        messages.info(self.request, "Тип продукта успешно удален")
        return reverse("dashboard:catalogue-class-list")


class AttributeOptionGroupCreateUpdateView(generic.UpdateView):
    template_name = "oscar/dashboard/catalogue/attribute_option_group_form.html"
    model = AttributeOptionGroup
    form_class = AttributeOptionGroupForm
    attribute_option_formset = AttributeOptionFormSet

    def process_all_forms(self, form):
        """
        This validates both the AttributeOptionGroup form and the
        AttributeOptions formset at once making it possible to display all their
        errors at once.
        """
        # pylint: disable=# pylint: disable=no-member
        if self.creating and form.is_valid():
            # the object will be needed by the attribute_option_formset
            self.object = form.save(commit=False)

        attribute_option_formset = self.attribute_option_formset(
            self.request.POST, self.request.FILES, instance=self.object
        )

        is_valid = form.is_valid() and attribute_option_formset.is_valid()

        if is_valid:
            return self.forms_valid(form, attribute_option_formset)
        else:
            return self.forms_invalid(form, attribute_option_formset)

    # pylint: disable=no-member
    def forms_valid(self, form, attribute_option_formset):
        form.save()
        attribute_option_formset.save()
        if self.is_popup:
            return self.popup_response(form.instance)
        else:
            return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, form, attribute_option_formset):
        messages.error(self.request, "Отправленные вами данные недействительны. Исправьте ошибки ниже.")
        ctx = self.get_context_data(
            form=form, attribute_option_formset=attribute_option_formset
        )
        return self.render_to_response(ctx)

    # form_valid and form_invalid are called depending on the validation result
    # of just the attribute option group form, and return a redirect to the
    # success URL or redisplay the form, respectively. In both cases we need to
    # check our formsets as well, so both methods do the same.
    # process_all_forms then calls forms_valid or forms_invalid respectively,
    # which do the redisplay or redirect.
    form_valid = form_invalid = process_all_forms

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault(
            "attribute_option_formset",
            self.attribute_option_formset(instance=self.object),
        )
        # pylint: disable=no-member
        ctx["title"] = self.get_title()
        return ctx

    def get_url_with_querystring(self, url):
        url_parts = [url]
        if self.request.GET.urlencode():
            url_parts += [self.request.GET.urlencode()]
        return "?".join(url_parts)


class AttributeOptionGroupCreateView(
    PopUpWindowCreateMixin, AttributeOptionGroupCreateUpdateView
):
    creating = True

    def get_object(self, queryset=None):
        return None

    def get_title(self):
        return "Создать группу параметров атрибута"

    def get_success_url(self):
        self.add_success_message("Группа параметров атрибута успешно создана")
        url = reverse("dashboard:catalogue-attribute-option-group-list")
        return self.get_url_with_querystring(url)


class AttributeOptionGroupUpdateView(
    PopUpWindowUpdateMixin, AttributeOptionGroupCreateUpdateView
):
    creating = False

    def get_object(self, queryset=None):
        attribute_option_group = get_object_or_404(
            AttributeOptionGroup, pk=self.kwargs["pk"]
        )
        return attribute_option_group

    def get_title(self):
        return "Обновить группу параметров атрибута '%s'" % self.object.name

    def get_success_url(self):
        self.add_success_message("Группа параметров атрибута успешно обновлена.")
        url = reverse("dashboard:catalogue-attribute-option-group-list")
        return self.get_url_with_querystring(url)


class AttributeOptionGroupListView(SingleTableView):
    template_name = "oscar/dashboard/catalogue/attribute_option_group_list.html"
    model = AttributeOptionGroup
    table_class = AttributeOptionGroupTable
    context_table_name = "attribute_option_groups"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["querystring"] = self.request.GET.urlencode()
        return ctx


class AttributeOptionGroupDeleteView(PopUpWindowDeleteMixin, generic.DeleteView):
    template_name = "oscar/dashboard/catalogue/attribute_option_group_delete.html"
    model = AttributeOptionGroup
    form_class = AttributeOptionGroupForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["title"] = "Удалить группу параметров атрибута '%s'" % self.object.name

        product_attribute_count = self.object.product_attributes.count()
        if product_attribute_count > 0:
            ctx["disallow"] = True
            ctx["title"] = "Невозможно удалить '%s'" % self.object.name
            messages.error(
                self.request, "%i Атрибуты продукта по-прежнему назначены этой группе параметров атрибутов."
                % product_attribute_count,
            )

        ctx["http_get_params"] = self.request.GET

        return ctx

    def get_url_with_querystring(self, url):
        url_parts = [url]
        http_post_params = self.request.POST.copy()
        try:
            del http_post_params["csrfmiddlewaretoken"]
        except KeyError:
            pass
        if http_post_params.urlencode():
            url_parts += [http_post_params.urlencode()]
        return "?".join(url_parts)

    def get_success_url(self):
        self.add_success_message("Группа параметров атрибута успешно удалена")
        url = reverse("dashboard:catalogue-attribute-option-group-list")
        return self.get_url_with_querystring(url)


class OptionListView(SingleTableView):
    template_name = "oscar/dashboard/catalogue/option_list.html"
    model = Option
    table_class = OptionTable
    context_table_name = "options"


class OptionCreateUpdateView(generic.UpdateView):
    template_name = "oscar/dashboard/catalogue/option_form.html"
    model = Option
    form_class = OptionForm

    # pylint: disable=no-member
    def form_valid(self, form):
        self.object = form.save()
        if self.is_popup:
            return self.popup_response(form.instance)
        else:
            return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # pylint: disable=no-member
        ctx["title"] = self.get_title()
        return ctx

    def form_invalid(self, form):
        messages.error(self.request, "Отправленные вами данные недействительны. Исправьте ошибки ниже.")
        return super().form_invalid(form)


class OptionCreateView(PopUpWindowCreateMixin, OptionCreateUpdateView):
    creating = True

    def get_object(self, queryset=None):
        return None

    def get_title(self):
        return "Добавить новую опцию"

    def get_success_url(self):
        self.add_success_message("Опция успешно создана")
        return reverse("dashboard:catalogue-option-list")


class OptionUpdateView(PopUpWindowUpdateMixin, OptionCreateUpdateView):
    creating = False

    def get_object(self, queryset=None):
        attribute_option_group = get_object_or_404(Option, pk=self.kwargs["pk"])
        return attribute_option_group

    def get_title(self):
        return "Обновить опцию '%s'" % self.object.name

    def get_success_url(self):
        self.add_success_message("Опция успешно обновлена")
        return reverse("dashboard:catalogue-option-list")


class OptionDeleteView(PopUpWindowDeleteMixin, generic.DeleteView):
    template_name = "oscar/dashboard/catalogue/option_delete.html"
    model = Option

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["title"] = "Удалить опцию '%s'" % self.object.name

        products = self.object.product_set
        products_count = products.count()
        product_classes = self.object.productclass_set
        product_classes_count = product_classes.count()

        if any([products_count, product_classes_count]):
            ctx["disallow"] = True
            ctx["title"] = "Невозможно удалить '%s'" % self.object.name
            if products_count:
                messages.error(self.request, "%i продукт(ы) по-прежнему относятся к этой опции. Список продуктов: %s. Удалите опцию у продукта(ов), прежде чем удалять опцию" % (products_count, list(products.values_list('title', flat=True))))
            if product_classes_count:
                messages.error(self.request, "%i класс(ы) продуктa(ов) по-прежнему присвоен(ы) этой опции. Список классов: %s. Удалите опцию у класса(ов), прежде чем удалять опцию" % (product_classes_count, list(product_classes.values_list('title', flat=True))))

        return ctx

    def get_success_url(self):
        self.add_success_message("Опция успешно удалена")
        return reverse("dashboard:catalogue-option-list")



class AdditionalListView(SingleTableView):
    template_name = "oscar/dashboard/catalogue/additional_list.html"
    model = Additional
    table_class = AdditionalTable
    context_table_name = "additional"


class AdditionalCreateUpdateView(generic.UpdateView):
    template_name = "oscar/dashboard/catalogue/additional_form.html"
    model = Additional
    form_class = AdditionalForm

    # pylint: disable=no-member
    def form_valid(self, form):
        self.object = form.save()
        if self.is_popup:
            return self.popup_response(form.instance)
        else:
            return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # pylint: disable=no-member
        ctx["title"] = self.get_title()
        return ctx

    def form_invalid(self, form):
        messages.error(self.request, "Отправленные вами данные недействительны. Исправьте ошибки ниже.")
        return super().form_invalid(form)


class AdditionalCreateView(PopUpWindowCreateMixin, AdditionalCreateUpdateView):
    creating = True

    def get_object(self, queryset=None):
        return None

    def get_title(self):
        return "Добавить новый доп. товар"

    def get_success_url(self):
        self.add_success_message("Опция успешно создана")
        return reverse("dashboard:catalogue-additional-list")


class AdditionalUpdateView(PopUpWindowUpdateMixin, AdditionalCreateUpdateView):
    creating = False

    def get_object(self, queryset=None):
        attribute_additional_group = get_object_or_404(Additional, pk=self.kwargs["pk"])
        return attribute_additional_group

    def get_title(self):
        return "Обновить дополнительный товар '%s'" % self.object.name

    def get_success_url(self):
        self.add_success_message("Дополнительный товар успешно обновлен")
        return reverse("dashboard:catalogue-additional-list")


class AdditionalDeleteView(PopUpWindowDeleteMixin, generic.DeleteView):
    template_name = "oscar/dashboard/catalogue/additional_delete.html"
    model = Additional
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["title"] = "Удалить дополнительный товар '%s'" % self.object.name

        products = self.object.product_set
        products_count = products.count()
        product_classes = self.object.productclass_set
        product_classes_count = product_classes.count()

        if any([products_count, product_classes_count]):
            ctx["disallow"] = True
            ctx["title"] = "Невозможно удалить '%s'" % self.object.name
            if products_count:
                messages.error(self.request, "%i продукт(ы) по-прежнему содержит этот доп продукт. Список продуктов с этим доп. продуктом: %s. Удалите доп.продукт у основного продукта(ов), прежде чем удалять доп. продукт" % (products_count, list(products.values_list('title', flat=True))))
            if product_classes_count:
                messages.error(self.request, "%i класс(ы) по-прежнему содержит этот доп продукт. Список класснов с этим доп. продуктом: %s. Удалите доп.продукт у класса(ов), прежде чем удалять доп. продукт" % (product_classes_count, list(product_classes.values_list('title', flat=True))))

        return ctx

    def get_success_url(self):
        self.add_success_message("Дополнительный товар успешно удален")
        return reverse("dashboard:catalogue-additional-list")
