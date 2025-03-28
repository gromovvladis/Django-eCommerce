import logging
from datetime import datetime
from itertools import chain

from apps.dashboard.evotor.mixins import EvotorTablesMixin
from apps.evotor.api.cloud import EvatorCloud
from apps.evotor.signals import (
    send_evotor_additionals,
    send_evotor_categories,
    send_evotor_products,
    update_site_additionals,
    update_site_groups,
    update_site_products,
    update_site_staffs,
    update_site_stores,
    update_site_terminals,
)
from apps.webshop.catalogue.serializers import (
    AdditionalsSerializer,
    ProductGroupsSerializer,
    ProductsSerializer,
)
from apps.webshop.store.serializers import StoresSerializer, TerminalsSerializer
from apps.webshop.user.serializers import StaffsSerializer
from core.loading import get_class, get_classes, get_model
from django.contrib import messages
from django.db.models import BooleanField, Case, Count, DecimalField, Max, Min, Q, When
from django.urls import reverse_lazy
from django_tables2 import SingleTableView

logger = logging.getLogger("apps.dashboard.evotor")

EvotorStoreForm = get_class("dashboard.evotor.forms", "EvotorStoreForm")
(
    EvotorStoreEvotorTable,
    EvotorStoreSiteTable,
    EvotorTerminalEvotorTable,
    EvotorTerminalSiteTable,
    EvotorStaffEvotorTable,
    EvotorStaffSiteTable,
    EvotorProductEvotorTable,
    EvotorProductSiteTable,
    EvotorAdditionalEvotorTable,
    EvotorAdditionalSiteTable,
    EvotorGroupEvotorTable,
    EvotorGroupSiteTable,
) = get_classes(
    "dashboard.evotor.tables",
    (
        "EvotorStoreEvotorTable",
        "EvotorStoreSiteTable",
        "EvotorTerminalEvotorTable",
        "EvotorTerminalSiteTable",
        "EvotorStaffEvotorTable",
        "EvotorStaffSiteTable",
        "EvotorProductEvotorTable",
        "EvotorProductSiteTable",
        "EvotorAdditionalEvotorTable",
        "EvotorAdditionalSiteTable",
        "EvotorGroupEvotorTable",
        "EvotorGroupSiteTable",
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


class EvotorStoreListView(EvotorTablesMixin):
    template_name = "dashboard/evotor/stores/store_list.html"
    model = Store
    serializer = StoresSerializer
    context_table_name = "tables"
    table_prefix = "store_{}-"
    table_evotor = EvotorStoreEvotorTable
    table_site = EvotorStoreSiteTable
    url_redirect = reverse_lazy("dashboard:evotor-stores")

    def get_json(self):
        """Получает JSON-данные от EvatorCloud"""
        return EvatorCloud().get_stores()

    def process_items(self, data_items):
        """Обрабатывает список магазинов, включая преобразование даты и проверку существования"""
        evotor_ids = set()
        for data_item in data_items:
            evotor_ids.add(data_item["id"])

        stores = {
            obj.evotor_id: obj for obj in Store.objects.filter(evotor_id__in=evotor_ids)
        }
        for data_item in data_items:
            data_item["updated_at"] = datetime.strptime(
                data_item["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z"
            )
            evotor_id, name = data_item["id"], data_item["name"]
            address = data_item.get("address", "")

            model_instance = stores.get(evotor_id)

            if model_instance:
                data_item["is_created"] = True
                data_item["is_valid"] = self._is_equal(
                    model_instance.name, name
                ) and self._is_equal(address, model_instance.primary_address)
            else:
                data_item["is_created"], data_item["is_valid"] = False, False

        return data_items

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


class EvotorTerminalListView(EvotorTablesMixin):
    template_name = "dashboard/evotor/terminals/terminal_list.html"
    model = Terminal
    serializer = TerminalsSerializer
    context_table_name = "tables"
    table_prefix = "terminal_{}-"
    table_evotor = EvotorTerminalEvotorTable
    table_site = EvotorTerminalSiteTable
    url_redirect = reverse_lazy("dashboard:evotor-terminals")

    def get_json(self):
        return EvatorCloud().get_terminals()

    def process_items(self, data_items):
        """Обрабатывает список терминалов, включая преобразование даты и проверку существования"""
        evotor_ids = set()
        for data_item in data_items:
            evotor_ids.add(data_item["id"])

        terminals = {
            obj.evotor_id: obj
            for obj in Terminal.objects.filter(evotor_id__in=evotor_ids)
        }

        for data_item in data_items:
            data_item["updated_at"] = datetime.strptime(
                data_item["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z"
            )
            evotor_id, name = data_item["id"], data_item["name"]
            store_id = data_item.get("store_id")
            model_instance = terminals.get(evotor_id)
            if model_instance:
                store_list = list(
                    model_instance.stores.values_list("evotor_id", flat=True)
                )
                data_item["is_created"], data_item["is_valid"], data_item["stores"] = (
                    True,
                    self._is_equal(name, model_instance.name)
                    and store_id in store_list,
                    store_list,
                )
            else:
                data_item["is_created"], data_item["is_valid"], data_item["stores"] = (
                    False,
                    False,
                    [store_id],
                )

        return data_items

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


class EvotorStaffListView(EvotorTablesMixin):
    template_name = "dashboard/evotor/staffs/staff_list.html"
    model = Staff
    serializer = StaffsSerializer
    context_table_name = "tables"
    table_prefix = "staff_{}-"
    table_evotor = EvotorStaffEvotorTable
    table_site = EvotorStaffSiteTable
    url_redirect = reverse_lazy("dashboard:evotor-staffs")

    def get_json(self):
        return EvatorCloud().get_staffs()

    def process_items(self, data_items):
        """Обрабатывает данные магазинов, проверяя их на создание и корректность"""
        evotor_ids = set()
        for data_item in data_items:
            evotor_ids.add(data_item["id"])

        staffs = {
            obj.evotor_id: obj for obj in Staff.objects.filter(evotor_id__in=evotor_ids)
        }

        for data_item in data_items:
            evotor_id = data_item["id"]
            data_item["updated_at"] = datetime.strptime(
                data_item["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z"
            )
            stores_ids = data_item.get("stores")
            model_instance = staffs.get(evotor_id)

            if model_instance:
                # Партнер существует: проверяем совпадение полей
                data_item["is_created"] = True
                data_item["stores"] = (
                    model_instance.user.stores.all() if model_instance.user else []
                )
                store_evotor_ids = {store.evotor_id for store in data_item["stores"]}
                store_matches = bool(store_evotor_ids.intersection(stores_ids))

                # Проверка совпадения данных
                data_item["is_valid"] = (
                    self._is_equal(model_instance.first_name, data_item.get("name"))
                    and self._is_equal(
                        model_instance.last_name, data_item.get("last_name")
                    )
                    and self._is_equal(
                        model_instance.middle_name,
                        data_item.get("patronymic_name"),
                    )
                    and store_matches
                )
            else:
                # Партнер не существует
                data_item.update(
                    {"stores": stores_ids, "is_created": False, "is_valid": False}
                )

        return data_items

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


class EvotorGroupsListView(EvotorTablesMixin):
    template_name = "dashboard/evotor/groups/group_list.html"
    model = Category
    form_class = EvotorStoreForm
    serializer = ProductGroupsSerializer
    context_table_name = "tables"
    table_prefix = "group_{}-"
    table_evotor = EvotorGroupEvotorTable
    table_site = EvotorGroupSiteTable
    url_redirect = reverse_lazy("dashboard:evotor-groups")

    def get_json(self):
        store_evotor_id = self.get_store_evotor_id()
        if store_evotor_id:
            return EvatorCloud().get_groups(store_evotor_id)
        else:
            messages.error(
                self.request,
                "Ошибка при формировании запроса к Эвотор. Не передан Эвотор ID Магазина. Обновите список магазинов.",
            )
            return []

    def process_items(self, data_items):
        parent_ids = set()
        store_ids = set()
        evotor_ids = set()

        for data_item in data_items:
            parent_id = data_item.get("parent_id", None)
            if parent_id is not None:
                parent_ids.add(parent_id)

            store_id = data_item.get("store_id", None)
            if store_id is not None:
                store_ids.add(store_id)

            evotor_ids.add(data_item["id"])

        # Получаем все объекты за один запрос для каждого типа модели
        parents = {
            obj.evotor_id: obj
            for obj in Category.objects.filter(evotor_id__in=parent_ids)
        }
        stores = {
            obj.evotor_id: obj for obj in Store.objects.filter(evotor_id__in=store_ids)
        }
        categories = {
            obj.evotor_id: obj
            for obj in Category.objects.filter(evotor_id__in=evotor_ids)
        }
        products = {
            obj.evotor_id: obj
            for obj in Product.objects.filter(evotor_id__in=evotor_ids)
        }

        # Обрабатываем каждый data_item
        for data_item in data_items:
            evotor_id = data_item["id"]
            data_item["updated_at"] = datetime.strptime(
                data_item["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z"
            )

            parent_id = data_item.get("parent_id", None)
            if parent_id is not None:
                data_item["parent"] = parents.get(parent_id) or products.get(parent_id)

            store_id = data_item.get("store_id", None)
            if store_id is not None:
                data_item["store"] = stores.get(store_id)

            model_instance = categories.get(evotor_id) or products.get(evotor_id)

            if model_instance:
                data_item["is_created"] = True
                parent_match = self._is_equal(
                    model_instance.get_evotor_parent_id(), parent_id
                )
                data_item["is_valid"] = (
                    self._is_equal(model_instance.name, data_item.get("name"))
                    and parent_match
                )
            else:
                if evotor_id == Additional.parent_id:
                    data_item.update({"is_created": True, "is_valid": True})
                else:
                    data_item.update({"is_created": False, "is_valid": False})

        return data_items

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

    def send_models(self, ids):
        send_evotor_categories.send(
            sender=self,
            category_ids=ids,
            user_id=self.request.user.id,
        )
        messages.info(
            self.request,
            "Список категорий и товаров с вариациями отправляется в Эвотор! Это может занять некоторое время.",
        )


class EvotorProductListView(EvotorTablesMixin):
    template_name = "dashboard/evotor/products/product_list.html"
    model = Product
    form_class = EvotorStoreForm
    serializer = ProductsSerializer
    context_table_name = "tables"
    table_prefix = "product_{}-"
    table_evotor = EvotorProductEvotorTable
    table_site = EvotorProductSiteTable
    url_redirect = reverse_lazy("dashboard:evotor-products")

    def get_json(self):
        store_evotor_id = self.get_store_evotor_id()
        if store_evotor_id:
            return EvatorCloud().get_primary_products(store_evotor_id)
        else:
            messages.error(
                self.request,
                "Ошибка при формировании запроса к Эвотор. Не передан Эвотор ID Магазина. Обновите список магазинов.",
            )
            return []

    def process_items(self, data_items):
        # Собираем все уникальные ID для каждого типа модели
        evotor_ids = set()
        store_ids = set()
        parent_ids = set()

        for data_item in data_items:
            evotor_ids.add(data_item["id"])
            store_ids.add(data_item["store_id"])
            parent_id = data_item.get("parent_id", None)
            if parent_id:
                parent_ids.add(parent_id)

        # Получаем все объекты за один запрос для каждого типа модели
        stores = {
            obj.evotor_id: obj for obj in Store.objects.filter(evotor_id__in=store_ids)
        }
        parent_categories = Category.objects.filter(evotor_id__in=parent_ids)
        parent_products = Product.objects.filter(evotor_id__in=parent_ids)
        parents = {
            obj.evotor_id: obj
            for obj in list(chain(parent_categories, parent_products))
        }
        model_instances = {
            obj.evotor_id: obj
            for obj in Product.objects.filter(evotor_id__in=evotor_ids)
        }

        # Обрабатываем каждый data_item
        for data_item in data_items:
            data_item["updated_at"] = datetime.strptime(
                data_item["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z"
            )

            evotor_id = data_item["id"]
            store_id = data_item["store_id"]

            store = stores.get(store_id)
            data_item["store"] = store

            parent_id = data_item.get("parent_id", None)
            if parent_id:
                data_item["parent"] = parents.get(parent_id)

            model_instance = model_instances.get(evotor_id)

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
                        and self._is_equal(stockrecord.price, data_item.get("price"))
                        and self._is_equal(
                            stockrecord.cost_price, data_item.get("cost_price")
                        )
                        and self._is_equal(
                            stockrecord.num_in_stock, data_item.get("quantity")
                        )
                        and self._is_equal(stockrecord.tax, data_item.get("tax"))
                        and self._is_equal(
                            stockrecord.is_public, data_item.get("allow_to_sell")
                        )
                    ) or False

                    product_class_match = self._is_equal(
                        model_instance.get_product_class().measure_name,
                        data_item.get("measure_name"),
                    )

                    data_item["is_valid"] = (
                        self._is_equal(
                            model_instance.get_name(),
                            data_item.get("name"),
                        )
                        and self._is_equal(
                            model_instance.article,
                            data_item.get("article_number"),
                        )
                        and self._is_equal(
                            model_instance.short_description,
                            data_item.get("description"),
                        )
                        and self._is_equal(
                            model_instance.get_evotor_parent_id(),
                            data_item.get("parent_id"),
                        )
                        and stockrecord_match
                        and product_class_match
                    )
                else:
                    data_item["is_valid"] = False

        return data_items

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

    def send_models(self, ids):
        send_evotor_products.send(
            sender=self,
            product_ids=ids,
            user_id=self.request.user.id,
        )
        messages.info(
            self.request,
            "Список товаров отправляется в Эвотор! Это может занять некоторое время.",
        )

    def get_site_table(self):
        evotor_ids = [model_qs["id"] for model_qs in self.queryset]
        correct_ids = [
            model_qs["id"] for model_qs in self.queryset if model_qs["is_valid"]
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


class EvotorAdditionalListView(EvotorTablesMixin):
    template_name = "dashboard/evotor/additionals/additional_list.html"
    model = Additional
    form_class = EvotorStoreForm
    serializer = AdditionalsSerializer
    context_table_name = "tables"
    table_prefix = "additional_{}-"
    table_evotor = EvotorAdditionalEvotorTable
    table_site = EvotorAdditionalSiteTable
    url_redirect = reverse_lazy("dashboard:evotor-additionals")

    def get_json(self):
        store_evotor_id = self.get_store_evotor_id()
        if store_evotor_id:
            return EvatorCloud().get_additionals_products(store_evotor_id)
        else:
            messages.error(
                self.request,
                "Ошибка при формировании запроса к Эвотор. Не передан Эвотор ID Магазина. Обновите список магазинов.",
            )
            return []

    def process_items(self, data_items):
        # Собираем все уникальные ID для каждого типа модели
        store_ids = set()
        evotor_ids = set()

        for data_item in data_items:
            store_ids.add(data_item["store_id"])
            evotor_ids.add(data_item["id"])

        # Получаем все объекты за один запрос для каждого типа модели
        stores = {
            obj.evotor_id: obj for obj in Store.objects.filter(evotor_id__in=store_ids)
        }
        model_instances = {
            obj.evotor_id: obj
            for obj in self.model.objects.filter(evotor_id__in=evotor_ids)
        }

        # Обрабатываем каждый data_item
        for data_item in data_items:
            data_item["updated_at"] = datetime.strptime(
                data_item["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z"
            )

            evotor_id = data_item["id"]
            store_id = data_item["store_id"]

            store = stores.get(store_id)
            data_item["store"] = store

            model_instance = model_instances.get(evotor_id)

            if not model_instance:
                data_item.update({"is_created": False, "is_valid": False})
            else:
                data_item["is_created"] = True
                if store:
                    model_stores = set(
                        model_instance.stores.values_list("evotor_id", flat=True)
                    )
                    data_item["is_valid"] = (
                        self._is_equal(
                            model_instance.get_name(),
                            data_item.get("name"),
                        )
                        and self._is_equal(
                            model_instance.article,
                            data_item.get("article_number"),
                        )
                        and self._is_equal(
                            model_instance.description,
                            data_item.get("description"),
                        )
                        and self._is_equal(
                            model_instance.get_evotor_parent_id(),
                            data_item.get("parent_id"),
                        )
                        and self._is_equal(
                            model_instance.is_public,
                            data_item.get("allow_to_sell"),
                        )
                        and self._is_equal(model_instance.tax, data_item.get("tax"))
                        and store_id in model_stores
                    )
                else:
                    data_item["is_valid"] = False

        return data_items

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

    def send_models(self, ids):
        send_evotor_additionals.send(
            sender=self,
            additional_ids=ids,
            user_id=self.request.user.id,
        )
        messages.info(
            self.request,
            "Список дополнительных товаров отправляется в Эвотор! Это может занять некоторое время.",
        )

    def get_site_table(self):
        evotor_ids = [model_qs["id"] for model_qs in self.queryset]
        correct_ids = [
            model_qs["id"] for model_qs in self.queryset if model_qs["is_valid"]
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


class EvotorDocsListView(SingleTableView):
    template_name = "dashboard/evotor/docs/doc_list.html"
    # form_class = EvotorDocForm
    # serializer = DocsSerializer
    context_table_name = "table"
    # table_site = EvotorDocSiteTable
    url_redirect = reverse_lazy("dashboard:evotor-docs")
