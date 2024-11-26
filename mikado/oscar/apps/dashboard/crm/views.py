from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import View

from oscar.apps.catalogue.serializers import ProductsGroupSerializer, ProductsSerializer
from oscar.apps.crm.client import EvatorCloud
from oscar.apps.customer.serializers import StaffsSerializer
from oscar.apps.dashboard.crm.mixins import CRMTablesMixin
from oscar.apps.store.serializers import StoresSerializer, TerminalsSerializer
from oscar.core.loading import get_class, get_classes, get_model

from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.base import View
from datetime import datetime

import logging

logger = logging.getLogger("oscar.dashboard")

Store = get_model("store", "Store")
Staff = get_model("user", "Staff")
Terminal = get_model("store", "Terminal")
Order = get_model("order", "Order")
Line = get_model("order", "Line")
Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")

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
        "CRMGroupEvotorTable",
        "CRMGroupSiteTable",
    ),
)


class CRMStoreListView(CRMTablesMixin):
    template_name = "oscar/dashboard/crm/stores/store_list.html"
    model = Store
    serializer = StoresSerializer
    context_table_name = "tables"
    table_prefix = "store_{}-"
    table_evotor = CRMStoreEvotorTable
    table_site = CRMStoreSiteTable
    url_redirect = reverse_lazy("dashboard:crm-stores")

    def get_queryset(self):

        data_json = EvatorCloud().get_stores()

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
                address = data_item.get("address")
                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()

                if model_instance:
                    # Партнер существует: проверяем совпадение полей
                    data_item["is_created"] = True
                    # Проверка совпадения полей
                    address_matches = address == (
                        model_instance.primary_address.line1
                        if model_instance.primary_address
                        else None
                    )
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
        msg, success = EvatorCloud().create_or_update_site_stores(
            data_items, is_filtered
        )

        if success:
            messages.success(self.request, msg)
        else:
            messages.error(self.request, msg)

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

    def get_queryset(self):
        data_json = EvatorCloud().get_terminals()

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
        msg, success = EvatorCloud().create_or_update_site_terminals(
            data_items, is_filtered
        )

        if success:
            messages.success(self.request, msg)
        else:
            messages.error(self.request, msg)

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

    def get_queryset(self):
        data_json = EvatorCloud().get_staffs()

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
                    store_matches = bool(store_evotor_ids.intersection(stores_ids))
                    data_item["is_valid"] = (
                        model_instance.first_name == first_name
                        and model_instance.last_name == last_name
                        and model_instance.middle_name == middle_name
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
        msg, success = EvatorCloud().create_or_update_site_staffs(
            data_items, is_filtered
        )

        if success:
            messages.success(self.request, msg)
        else:
            messages.error(self.request, msg)

        return redirect(self.url_redirect)


class CRMGroupsListView(CRMTablesMixin):
    template_name = "oscar/dashboard/crm/groups/group_list.html"
    model = Category
    form_class = CRMStoreForm
    serializer = ProductsGroupSerializer
    context_table_name = "tables"
    table_prefix = "group_{}-"
    table_evotor = CRMGroupEvotorTable
    table_site = CRMGroupSiteTable
    url_redirect = reverse_lazy("dashboard:crm-groups")

    def get_queryset(self):
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

        data_json = EvatorCloud().get_groups(store_evotor_id)

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

                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()

                if model_instance:
                    data_item["is_created"] = True
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
        msg, success = EvatorCloud().create_or_update_site_groups(
            data_items, is_filtered
        )

        if success:
            messages.success(self.request, msg)
        else:
            messages.error(self.request, msg)

        return redirect(self.url_redirect)

    # def send_models(self, is_filtered):
    #     models = super().send_models(is_filtered)
    #     try:
    #         products, error = EvatorCloud().update_or_create_evotor_products(models)
    #     except Exception as e:
    #         logger.error("Ошибка при отправке созданного / измененного товара в Эвотор. Ошибка %s", e)
        
    #     if error:
    #         messages.error(self.request, error)
    #     else:
    #         messages.success(self.request, "Товары успешно отправлены в Эвотор.")

    #     return redirect(self.url_redirect)

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

    def get_queryset(self):

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

        data_json = EvatorCloud().get_products(store_evotor_id)
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

                parent_id = data_item.get("parent_id")
                data_item["parent"] = (
                    Category.objects.filter(evotor_id=parent_id).first()
                    or Product.objects.filter(evotor_id=parent_id).first()
                    or parent_id
                )

                model_instance = self.model.objects.filter(evotor_id=evotor_id).first()

                if not model_instance:
                    data_item.update({"is_created": False, "is_valid": False})
                else:
                    data_item["is_created"] = True
                    if store:
                        stockrecord = model_instance.stockrecords.filter(store__evotor_id=store_id).first()

                        stockrecord_match = (
                            stockrecord
                            # and stockrecord.evotor_code == data_item.get("code")
                            and stockrecord.price == data_item.get("price", 0)
                            and stockrecord.cost_price == data_item.get("cost_price", 0)
                            and stockrecord.num_in_stock == data_item.get("quantity", 0)
                            and stockrecord.tax == data_item.get("tax")
                            and stockrecord.is_public == data_item.get("allow_to_sell", False)
                        )
                        product_class_match = (
                            model_instance.get_product_class().measure_name
                            == data_item.get("measure_name")
                        )
                        data_item["is_valid"] = (
                            model_instance.title == data_item.get("name", "").strip()
                            and model_instance.upc == data_item.get("article_number", None)
                            and model_instance.short_description == data_item.get("description", "").strip()
                            and model_instance.get_evotor_parent() == data_item.get("parent_id", None)
                            and stockrecord_match
                            and product_class_match
                        )
                    else:
                        data_item["is_valid"] = False

            self.queryset = sorted(data_items, key=lambda x: (x["is_created"], x["is_valid"]))

            return self.queryset
        else:
            self.queryset = []
            logger.error(f"Ошибка при сериализации данных {serializer.errors}")
            messages.error(self.request,(f"Ошибка при сериализации данных {serializer.errors}"))
            return self.queryset

    def update_models(self, data_items, is_filtered):
        msg, success = EvatorCloud().create_or_update_site_products(
            data_items, is_filtered
        )

        if success:
            messages.success(self.request, msg)
        else:
            messages.error(self.request, msg)

        return self.redirect_with_get_params(self.url_redirect, self.request)

    def send_models(self, is_filtered):
        models = super().send_models(is_filtered)
        try:
            products, error = EvatorCloud().update_or_create_evotor_products(models)
        except Exception as e:
            logger.error("Ошибка при отправке созданного / измененного товара в Эвотор. Ошибка %s", e)
        
        if error:
            messages.error(self.request, error)
        else:
            messages.success(self.request, "Товары успешно отправлены в Эвотор.")

        return redirect(self.url_redirect)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        return ctx


class CRMDocsListView(View):
    pass


class CRMAcceptListView(View):
    pass


class CRMRevaluationListView(View):
    pass


class CRMWriteOffListView(View):
    pass


class CRMInventoryListView(View):
    pass


class CRMSessionListView(View):
    pass


class CRMCashListView(View):
    pass


class CRMReportListView(View):
    pass


class CRMEventListView(View):
    pass