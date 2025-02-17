import logging
from datetime import datetime

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import View
from django.db.models import Count, Max, Min, Case, When, DecimalField, BooleanField, Q
from django_tables2 import SingleTableView

from oscar.core.loading import get_class, get_classes, get_model
from oscar.apps.crm.client import EvatorCloud
from oscar.apps.customer.serializers import StaffsSerializer
from oscar.apps.dashboard.crm.mixins import CRMTablesMixin
from oscar.apps.store.serializers import StoresSerializer, TerminalsSerializer
from oscar.apps.catalogue.serializers import (
    AdditionalsSerializer,
    ProductGroupsSerializer,
    ProductsSerializer,
)
from oscar.apps.crm.signals import (
    update_site_stores,
    update_site_terminals,
    update_site_staffs,
    update_site_groups,
    update_site_products,
    update_site_additionals,
    send_evotor_categories,
    send_evotor_products,
)

logger = logging.getLogger("oscar.dashboard")

CRMStoreForm = get_class("dashboard.crm.forms", "CRMStoreForm")
(
    CRMStoreEvotorTable,
    CRMStoreSiteTable,
    CRMTerminalEvotorTable,
    CRMTerminalSiteTable,
    CRMStaffEvotorTable,
    CRMStaffSiteTable,
    CRMProductEvotorTable,
    CRMProductSiteTable,
    CRMAdditionalEvotorTable,
    CRMAdditionalSiteTable,
    CRMGroupEvotorTable,
    CRMGroupSiteTable,
) = get_classes(
    "dashboard.crm.tables",
    (
        "CRMStoreEvotorTable",
        "CRMStoreSiteTable",
        "CRMTerminalEvotorTable",
        "CRMTerminalSiteTable",
        "CRMStaffEvotorTable",
        "CRMStaffSiteTable",
        "CRMProductEvotorTable",
        "CRMProductSiteTable",
        "CRMAdditionalEvotorTable",
        "CRMAdditionalSiteTable",
        "CRMGroupEvotorTable",
        "CRMGroupSiteTable",
    ),
)

Store = get_model("store", "Store")
Staff = get_model("user", "Staff")
Terminal = get_model("store", "Terminal")
Order = get_model("order", "Order")
Line = get_model("order", "Line")
Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
Additional = get_model("catalogue", "Additional")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")


class CRMStoreListView(CRMTablesMixin):
    template_name = "oscar/dashboard/crm/stores/store_list.html"
    model = Store
    serializer = StoresSerializer
    context_table_name = "tables"
    table_prefix = "store_{}-"
    table_evotor = CRMStoreEvotorTable
    table_site = CRMStoreSiteTable
    url_redirect = reverse_lazy("dashboard:crm-stores")

    def get_json(self):
        return EvatorCloud().get_stores()

    def get_queryset(self):
        data_json = self.get_json()
        error = data_json.get("error")
        if error:
            self.queryset = []
            logger.error(f"Ошибка {error}")
            messages.error(self.request, error)
            return self.queryset

        serializer = self.serializer(data=data_json)

        if serializer.is_valid():
            data_items = serializer.initial_data["items"]

            for data_item in data_items:
                evotor_id = data_item["id"]
                data_item["updated_at"] = datetime.strptime(
                    data_item["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z"
                )
                name = data_item["name"]
                address = data_item.get("address", "")
                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()

                if model_instance:
                    # Партнер существует: проверяем совпадение полей
                    data_item["is_created"] = True
                    # Проверка совпадения полей
                    address_matches = address == getattr(model_instance, "address", "")
                    data_item["is_valid"] = (
                        model_instance.name == name and address_matches
                    )
                else:
                    # Партнер не существует
                    data_item["is_created"] = False
                    data_item["is_valid"] = False

            self.queryset = sorted(
                data_items, key=lambda x: (x["is_created"], x["is_valid"])
            )
            return self.queryset
        else:
            self.queryset = []
            logger.error(f"Ошибка при сериализации данных {serializer.errors}")
            messages.error(
                self.request,
                (f"Ошибка при сериализации данных {serializer.errors}"),
            )
            return self.queryset

    def update_models(self, data_items, is_filtered):
        update_site_stores.send(
            sender=self,
            data_items=data_items,
            is_filtered=is_filtered,
            user_id=self.request.user.id,
        )
        messages.info(
            self.request,
            "Список магазинов обновляется! Это может занять некоторое время.",
        )
        return redirect(self.url_redirect)


class CRMTerminalListView(CRMTablesMixin):
    template_name = "oscar/dashboard/crm/terminals/terminal_list.html"
    model = Terminal
    serializer = TerminalsSerializer
    context_table_name = "tables"
    table_prefix = "terminal_{}-"
    table_evotor = CRMTerminalEvotorTable
    table_site = CRMTerminalSiteTable
    url_redirect = reverse_lazy("dashboard:crm-terminals")

    def get_json(self):
        return EvatorCloud().get_terminals()

    def get_queryset(self):
        data_json = self.get_json()
        error = data_json.get("error")
        if error:
            self.queryset = []
            logger.error(f"Ошибка {error}")
            messages.error(self.request, error)
            return self.queryset

        serializer = self.serializer(data=data_json)

        if serializer.is_valid():
            data_items = serializer.initial_data["items"]

            for data_item in data_items:
                evotor_id = data_item["id"]
                data_item["updated_at"] = datetime.strptime(
                    data_item["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z"
                )
                name = data_item["name"]
                store_id = data_item.get("store_id")
                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()

                if model_instance:
                    # Партнер существует: проверяем совпадение полей
                    data_item["is_created"] = True
                    data_item["stores"] = model_instance.stores.all()
                    # Проверка совпадения полей
                    store_matches = store_id in model_instance.stores.values_list(
                        "evotor_id", flat=True
                    )
                    data_item["is_valid"] = (
                        model_instance.name == name and store_matches
                    )
                else:
                    # Партнер не существует
                    data_item["stores"] = [store_id]
                    data_item["is_created"] = False
                    data_item["is_valid"] = False

            self.queryset = sorted(
                data_items, key=lambda x: (x["is_created"], x["is_valid"])
            )
            return self.queryset
        else:
            self.queryset = []
            logger.error(f"Ошибка при сериализации данных {serializer.errors}")
            messages.error(
                self.request,
                (f"Ошибка при сериализации данных {serializer.errors}"),
            )
            return self.queryset

    def update_models(self, data_items, is_filtered):
        update_site_terminals.send(
            sender=self,
            data_items=data_items,
            is_filtered=is_filtered,
            user_id=self.request.user.id,
        )
        messages.info(
            self.request,
            "Список терминалов обновляется! Это может занять некоторое время.",
        )
        return redirect(self.url_redirect)


class CRMStaffListView(CRMTablesMixin):
    template_name = "oscar/dashboard/crm/staffs/staff_list.html"
    model = Staff
    serializer = StaffsSerializer
    context_table_name = "tables"
    table_prefix = "staff_{}-"
    table_evotor = CRMStaffEvotorTable
    table_site = CRMStaffSiteTable
    url_redirect = reverse_lazy("dashboard:crm-staffs")

    def get_json(self):
        return EvatorCloud().get_staffs()

    def get_queryset(self):
        data_json = self.get_json()
        error = data_json.get("error")
        if error:
            self.queryset = []
            logger.error(f"Ошибка {error}")
            messages.error(self.request, error)
            return self.queryset

        serializer = self.serializer(data=data_json)

        if serializer.is_valid():
            data_items = serializer.initial_data["items"]

            for data_item in data_items:
                evotor_id = data_item["id"]
                data_item["updated_at"] = datetime.strptime(
                    data_item["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z"
                )
                first_name = data_item.get("name", None)
                last_name = data_item.get("last_name", None)
                middle_name = data_item.get("patronymic_name", None)
                stores_ids = data_item.get("stores", None)
                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()

                if model_instance:
                    data_item["is_created"] = True
                    data_item["stores"] = (
                        model_instance.user.stores.all() if model_instance.user else []
                    )
                    store_evotor_ids = (
                        set(
                            model_instance.user.stores.values_list(
                                "evotor_id", flat=True
                            )
                        )
                        if model_instance.user
                        else set()
                    )

                    def is_equal(value1, value2):
                        return (
                            value1 in [None, ""]
                            if value2 in [None, ""]
                            else value1 == value2
                        )

                    store_matches = bool(store_evotor_ids.intersection(stores_ids))
                    data_item["is_valid"] = (
                        is_equal(model_instance.first_name, first_name)
                        and is_equal(model_instance.last_name, last_name)
                        and is_equal(model_instance.middle_name, middle_name)
                        and store_matches
                    )
                else:
                    data_item.update(
                        {"stores": stores_ids, "is_created": False, "is_valid": False}
                    )

            self.queryset = sorted(
                data_items, key=lambda x: (x["is_created"], x["is_valid"])
            )
            return self.queryset
        else:
            self.queryset = []
            logger.error(f"Ошибка при сериализации данных {serializer.errors}")
            messages.error(
                self.request,
                (f"Ошибка при сериализации данных {serializer.errors}"),
            )
            return self.queryset

    def update_models(self, data_items, is_filtered):
        update_site_staffs.send(
            sender=self,
            data_items=data_items,
            is_filtered=is_filtered,
            user_id=self.request.user.id,
        )
        messages.info(
            self.request,
            "Список сотрудников обновляется! Это может занять некоторое время.",
        )
        return redirect(self.url_redirect)


class CRMGroupsListView(CRMTablesMixin):
    template_name = "oscar/dashboard/crm/groups/group_list.html"
    model = Category
    form_class = CRMStoreForm
    serializer = ProductGroupsSerializer
    context_table_name = "tables"
    table_prefix = "group_{}-"
    table_evotor = CRMGroupEvotorTable
    table_site = CRMGroupSiteTable
    url_redirect = reverse_lazy("dashboard:crm-groups")

    def get_json(self):
        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            messages.error(
                self.request,
                "Ошибка при формировании запроса к Эвотор. Неверные данные формы",
            )
            return []

        data = self.form.cleaned_data
        store_evotor_id = data.get("store") or self.form.fields.get("store").initial

        if not store_evotor_id:
            messages.error(
                self.request,
                "Ошибка при формировании запроса к Эвотор. Не передан Эвотор ID Магазина. Обновите список точек продаж",
            )
            return []

        return EvatorCloud().get_groups(store_evotor_id)

    def get_queryset(self):
        data_json = self.get_json()
        error = data_json.get("error")
        if error:
            self.queryset = []
            logger.error(f"Ошибка {error}")
            messages.error(
                self.request,
                error,
            )
            return self.queryset

        serializer = self.serializer(data=data_json)

        if serializer.is_valid():
            data_items = serializer.initial_data["items"]

            for data_item in data_items:
                evotor_id = data_item["id"]
                data_item["updated_at"] = datetime.strptime(
                    data_item["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z"
                )

                parent_id = data_item.get("parent_id", None)
                if parent_id is not None:
                    data_item["parent"] = (
                        Category.objects.filter(evotor_id=parent_id).first()
                        or Product.objects.filter(evotor_id=parent_id).first()
                    )

                store_id = data_item.get("store_id", None)
                if store_id is not None:
                    data_item["store"] = Store.objects.filter(
                        evotor_id=store_id
                    ).first()

                try:
                    model_instance = Category.objects.get(evotor_id=evotor_id)
                except Category.DoesNotExist:
                    model_instance = Product.objects.filter(evotor_id=evotor_id).first()

                if model_instance:
                    data_item["is_created"] = True
                    name = data_item.get("name", None)
                    parent_match = (
                        model_instance.get_parent() is None
                        or parent_id is None
                        or model_instance.get_parent().evotor_id == parent_id
                    )
                    data_item["is_valid"] = model_instance.name == name and parent_match
                else:
                    if evotor_id == Additional.parent_id:
                        data_item.update({"is_created": True, "is_valid": True})
                    else:
                        data_item.update({"is_created": False, "is_valid": False})

            self.queryset = sorted(
                data_items, key=lambda x: (x["is_created"], x["is_valid"])
            )
            return self.queryset
        else:
            self.queryset = []
            logger.error(f"Ошибка при сериализации данных {serializer.errors}")
            messages.error(
                self.request,
                (f"Ошибка при сериализации данных {serializer.errors}"),
            )
            return self.queryset

    def update_models(self, data_items, is_filtered):
        update_site_groups.send(
            sender=self,
            data_items=data_items,
            is_filtered=is_filtered,
            user_id=self.request.user.id,
        )
        messages.info(
            self.request,
            "Список категорий и товаров с вариациями обновляется! Это может занять некоторое время.",
        )
        return redirect(self.url_redirect)

    def send_models(self, is_filtered):
        category_ids = super().send_models(is_filtered)
        send_evotor_categories.send(
            sender=self,
            category_ids=category_ids,
            user_id=self.request.user.id,
        )
        messages.info(
            self.request,
            "Список категорий и товаров с вариациями отправляется в Эвотор! Это может занять некоторое время.",
        )
        return redirect(self.url_redirect)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        return ctx


class CRMProductListView(CRMTablesMixin):
    template_name = "oscar/dashboard/crm/products/product_list.html"
    model = Product
    form_class = CRMStoreForm
    serializer = ProductsSerializer
    context_table_name = "tables"
    table_prefix = "product_{}-"
    table_evotor = CRMProductEvotorTable
    table_site = CRMProductSiteTable
    url_redirect = reverse_lazy("dashboard:crm-products")

    def get_json(self):
        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            messages.error(
                self.request,
                "Ошибка при формировании запроса к Эвотор. Неверные данные формы",
            )
            return []

        data = self.form.cleaned_data
        store_evotor_id = data.get("store") or self.form.fields.get("store").initial

        if not store_evotor_id:
            messages.error(
                self.request,
                "Ошибка при формировании запроса к Эвотор. Не передан Эвотор ID Магазина. Обновите список точек продаж",
            )
            return []

        return EvatorCloud().get_primary_products(store_evotor_id)

    def get_queryset(self):
        data_json = self.get_json()
        error = data_json.get("error")

        if error:
            self.queryset = []
            logger.error(f"Ошибка {error}")
            messages.error(self.request, error)
            return self.queryset

        serializer = self.serializer(data=data_json)
        if serializer.is_valid():
            data_items = serializer.initial_data["items"]

            for data_item in data_items:
                data_item["updated_at"] = datetime.strptime(
                    data_item["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z"
                )

                evotor_id = data_item["id"]
                store_id = data_item["store_id"]

                store = Store.objects.filter(evotor_id=store_id).first()
                data_item["store"] = store
                data_item["is_valid"] = bool(store)

                parent_id = data_item.get("parent_id", None)
                if parent_id:
                    data_item["parent"] = (
                        Category.objects.filter(evotor_id=parent_id).first()
                        or Product.objects.filter(evotor_id=parent_id).first()
                        or Additional.parent_id == parent_id
                    )

                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()

                if not model_instance:
                    data_item.update({"is_created": False, "is_valid": False})
                else:
                    data_item["is_created"] = True
                    if store:
                        stockrecord = model_instance.stockrecords.filter(
                            store__evotor_id=store_id
                        ).first()
                        stockrecord_match = (
                            stockrecord
                            # and stockrecord.evotor_code == data_item.get("code")
                            and stockrecord.price == data_item.get("price", 0)
                            and stockrecord.cost_price == data_item.get("cost_price", 0)
                            and stockrecord.num_in_stock == data_item.get("quantity", 0)
                            and stockrecord.tax == data_item.get("tax")
                            and stockrecord.is_public
                            == data_item.get("allow_to_sell", False)
                        ) or False

                        product_class_match = (
                            model_instance.get_product_class().measure_name
                            == data_item.get("measure_name")
                        )
                        data_item["is_valid"] = (
                            model_instance.name == data_item.get("name", "").strip()
                            and model_instance.article
                            == data_item.get("article_number", "").strip()
                            and model_instance.short_description
                            == data_item.get("description", None)
                            and model_instance.get_evotor_parent_id()
                            == data_item.get("parent_id", None)
                            and stockrecord_match
                            and product_class_match
                        )
                    else:
                        data_item["is_valid"] = False

            self.queryset = sorted(
                data_items, key=lambda x: (x["is_created"], x["is_valid"])
            )

            return self.queryset
        else:
            self.queryset = []
            logger.error(f"Ошибка при сериализации данных {serializer.errors}")
            messages.error(
                self.request, (f"Ошибка при сериализации данных {serializer.errors}")
            )
            return self.queryset

    def update_models(self, data_items, is_filtered):
        update_site_products.send(
            sender=self,
            data_items=data_items,
            is_filtered=is_filtered,
            user_id=self.request.user.id,
        )
        messages.info(
            self.request,
            "Список товаров обновляется! Это может занять некоторое время.",
        )
        return self.redirect_with_get_params(self.url_redirect, self.request)

    def send_models(self, is_filtered):
        product_ids = super().send_models(is_filtered)
        send_evotor_products.send(
            sender=self,
            product_ids=product_ids,
            user_id=self.request.user.id,
        )
        messages.info(
            self.request,
            "Список категорий и товаров с вариациями отправляется в Эвотор! Это может занять некоторое время.",
        )
        return redirect(self.url_redirect)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        return ctx

    def get_site_table(self):
        evotor_ids = [model_qs["id"] for model_qs in self.queryset]
        correct_ids = [
            model_qs["id"] for model_qs in self.queryset if model_qs["is_valid"] == True
        ]

        data = self.form.cleaned_data
        store_id = data.get("store") or self.form.fields.get("store").initial

        site_models = (
            self.model.objects.filter(
                Q(stockrecords__store__evotor_id=store_id)
                | Q(children__stockrecords__store__evotor_id=store_id)
            )
            .annotate(
                is_valid=Case(
                    When(
                        Q(evotor_id__in=evotor_ids) & Q(evotor_id__in=correct_ids),
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
                wrong_evotor_id=Case(
                    When(
                        Q(evotor_id__isnull=False) & ~Q(evotor_id__in=evotor_ids),
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
                min_price=Case(
                    When(structure="parent", then=Min("children__stockrecords__price")),
                    default=Min("stockrecords__price"),
                    output_field=DecimalField(),
                ),
                max_price=Case(
                    When(structure="parent", then=Max("children__stockrecords__price")),
                    default=Max("stockrecords__price"),
                    output_field=DecimalField(),
                ),
                old_price=Case(
                    When(
                        structure="parent",
                        then=Max("children__stockrecords__old_price"),
                    ),
                    default=Max("stockrecords__old_price"),
                    output_field=DecimalField(),
                ),
                variants=Count("children"),
            )
            .order_by("-wrong_evotor_id", "is_valid", "evotor_id", "-is_valid")
        )

        return self.table_site(site_models)


class CRMAdditionalListView(CRMTablesMixin):
    template_name = "oscar/dashboard/crm/additionals/additional_list.html"
    model = Additional
    form_class = CRMStoreForm
    serializer = AdditionalsSerializer
    context_table_name = "tables"
    table_prefix = "additional_{}-"
    table_evotor = CRMAdditionalEvotorTable
    table_site = CRMAdditionalSiteTable
    url_redirect = reverse_lazy("dashboard:crm-additionals")

    def get_json(self):
        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            messages.error(
                self.request,
                "Ошибка при формировании запроса к Эвотор. Неверные данные формы",
            )
            return []

        data = self.form.cleaned_data
        store_evotor_id = data.get("store") or self.form.fields.get("store").initial

        if not store_evotor_id:
            messages.error(
                self.request,
                "Ошибка при формировании запроса к Эвотор. Не передан Эвотор ID Магазина. Обновите список точек продаж",
            )
            return []

        return EvatorCloud().get_additionals_products(store_evotor_id)

    def get_queryset(self):
        data_json = self.get_json()
        error = data_json.get("error")

        if error:
            self.queryset = []
            logger.error(f"Ошибка {error}")
            messages.error(self.request, error)
            return self.queryset

        serializer = self.serializer(data=data_json)
        if serializer.is_valid():
            data_items = serializer.initial_data["items"]

            for data_item in data_items:
                data_item["updated_at"] = datetime.strptime(
                    data_item["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z"
                )

                evotor_id = data_item["id"]
                store_id = data_item["store_id"]

                store = Store.objects.filter(evotor_id=store_id).first()
                data_item["store"] = store
                data_item["is_valid"] = bool(store)

                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()

                if not model_instance:
                    data_item.update({"is_created": False, "is_valid": False})
                else:
                    data_item["is_created"] = True
                    if store:
                        data_item["is_valid"] = (
                            model_instance.name == data_item.get("name", "").strip()
                            and model_instance.article
                            == data_item.get("article_number", "").strip()
                            and model_instance.description
                            == data_item.get("description", None)
                            and model_instance.parent_id
                            == data_item.get("parent_id", None)
                            and data_item.get("store_id", None)
                            in model_instance.stores.values_list("evotor_id", flat=True)
                            and model_instance.is_public
                            == data_item.get("allow_to_sell", None)
                            and model_instance.tax == data_item.get("tax", None)
                        )
                    else:
                        data_item["is_valid"] = False

            self.queryset = sorted(
                data_items, key=lambda x: (x["is_created"], x["is_valid"])
            )

            return self.queryset
        else:
            self.queryset = []
            logger.error(f"Ошибка при сериализации данных {serializer.errors}")
            messages.error(
                self.request, (f"Ошибка при сериализации данных {serializer.errors}")
            )
            return self.queryset

    def update_models(self, data_items, is_filtered):
        update_site_additionals.send(
            sender=self,
            data_items=data_items,
            is_filtered=is_filtered,
            user_id=self.request.user.id,
        )
        messages.info(
            self.request,
            "Список дополнительных товаров обновляется! Это может занять некоторое время.",
        )
        return self.redirect_with_get_params(self.url_redirect, self.request)

    def send_models(self, is_filtered):
        additional_ids = super().send_models(is_filtered)
        send_evotor_products.send(
            sender=self,
            additional_ids=additional_ids,
            user_id=self.request.user.id,
        )
        messages.info(
            self.request,
            "Список дополнительных товаров отправляется в Эвотор! Это может занять некоторое время.",
        )
        return redirect(self.url_redirect)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        return ctx

    def get_site_table(self):
        evotor_ids = [model_qs["id"] for model_qs in self.queryset]
        correct_ids = [
            model_qs["id"] for model_qs in self.queryset if model_qs["is_valid"] == True
        ]

        site_models = (
            self.model.objects.all()
            .annotate(
                is_valid=Case(
                    When(
                        Q(evotor_id__in=evotor_ids) & Q(evotor_id__in=correct_ids),
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
                wrong_evotor_id=Case(
                    When(
                        Q(evotor_id__isnull=False) & ~Q(evotor_id__in=evotor_ids),
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
            )
            .order_by("-wrong_evotor_id", "is_valid", "evotor_id", "-is_valid")
        )

        return self.table_site(site_models)


class CRMDocsListView(SingleTableView):
    template_name = "oscar/dashboard/crm/docs/doc_list.html"
    # form_class = CRMDocForm
    # serializer = DocsSerializer
    context_table_name = "table"
    # table_site = CRMDocSiteTable
    url_redirect = reverse_lazy("dashboard:crm-docs")
