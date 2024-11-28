# pylint: disable=attribute-defined-outside-init
import re
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django_tables2 import SingleTableView

from django.db.models import Q, F

from django.contrib.auth.models import Group

from oscar.apps.communication.notifications.views import DetailView
from oscar.apps.dashboard.users.views import CustomerListView
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_classes, get_model

from django.views.generic import CreateView, UpdateView, DeleteView, View
from django_tables2 import SingleTableView
from django.db.models import Exists, OuterRef, BooleanField

User = get_user_model()
Staff = get_model("user", "Staff")
Store = get_model("store", "Store")
Terminal = get_model("store", "Terminal")
(
    StoreSearchForm,
    StoreForm,
) = get_classes(
    "dashboard.stores.forms",
    [
        "StoreSearchForm",
        "StoreForm",
    ],
)
StaffForm = get_class("dashboard.users.forms","StaffForm")
GroupForm = get_class("dashboard.users.forms","GroupForm")
StoreListTable = get_class("dashboard.stores.tables", "StoreListTable")
GroupListTable = get_class("dashboard.stores.tables", "GroupListTable")
StaffListTable = get_class("dashboard.stores.tables", "StaffListTable")
TerminalListTable = get_class("dashboard.stores.tables", "TerminalListTable")
StoreStaffListTable = get_class("dashboard.stores.tables", "StoreStaffListTable")


class StoreListView(SingleTableView):
    context_table_name = "stores"
    template_name = "oscar/dashboard/stores/store_list.html"
    form_class = StoreSearchForm
    table_class = StoreListTable

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)

        if self.form.is_valid() and any(self.form.cleaned_data.values()):
            table.caption = "Результаты поиска: %s" % self.object_list.count()

        return table
    
    def get_table_pagination(self, table):
        return dict(per_page=settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["queryset_description"] = self.description
        ctx["form"] = self.form
        ctx["is_filtered"] = self.is_filtered
        return ctx  

    def get_queryset(self):
        qs = Store._default_manager.prefetch_related("addresses", "users", "users__profile").all()

        self.description = "Все магазины"

        # We track whether the queryset is filtered to determine whether we
        # show the search form 'reset' button.
        self.is_filtered = False
        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return qs

        qs = self.apply_search(qs)

        return qs

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

        name = data.get("name")
        if name:
            queryset = queryset.filter(name__icontains=data["name"])
            self.is_filtered = True

        return queryset.distinct()


class StoreCreateView(CreateView):
    model = Store
    template_name = "oscar/dashboard/stores/store_form.html"
    form_class = StoreForm
    success_url = reverse_lazy("dashboard:store-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Создать магазин"
        return ctx

    def get_success_url(self):
        messages.success(
            self.request, "Магазин '%s' успешно создан. Доступно добавление персонала." % self.object.name
        )
        # Используем reverse для получения строки URL
        return reverse("dashboard:store-manage", kwargs={"pk": self.object.id})
        
    def form_valid(self, form):
        self.object = form.save()
        self.object.address = self.object.addresses.model(store=self.object)
        self.object.address.line1 = form.cleaned_data["line1"]
        self.object.address.coords_long = form.cleaned_data["coords_long"]
        self.object.address.coords_lat = form.cleaned_data["coords_lat"]
        self.object.address.save()
        return super().form_valid(form)


class StoreManageView(UpdateView):
    """
    This multi-purpose view renders out a form to edit the store's details,
    the associated address and a list of all associated users.
    """
    model = Store
    template_name = "oscar/dashboard/stores/store_manage.html"
    form_class = StoreForm
    success_url = reverse_lazy("dashboard:store-list")

    def get_object(self, queryset=None):
        self.store = get_object_or_404(Store, pk=self.kwargs["pk"])
        self.address = self.store.primary_address
        if self.address is None:
            self.address = self.store.addresses.model(store=self.store)
        return self.store

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["store"] = self.store
        ctx["title"] = self.store.name
        ctx["users"] = self.store.users.all()
        ctx["terminals"] = self.store.terminals.all()
        if self.address.line1:
            ctx['line1'] = self.address.line1
        return ctx

    def form_valid(self, form):
        self.object = form.save()
        self.object.address = self.address
        self.object.address.line1 = form.cleaned_data["line1"]
        self.object.address.coords_long = form.cleaned_data["coords_long"]
        self.object.address.coords_lat = form.cleaned_data["coords_lat"]
        self.object.address.save()
        messages.success(
            self.request,
            "Магазин '%s' успешно обновлен." % self.object.name,
        )
        return super().form_valid(form)


class StoreDeleteView(DeleteView):
    model = Store
    template_name = "oscar/dashboard/stores/store_delete.html"

    def get_success_url(self):
        messages.success(
            self.request, "Магазин '%s' успешно удален." % self.object.name
        )
        return reverse("dashboard:store-list")



# =====
# Terminals
# =====


class TerminalListView(SingleTableView):
    context_table_name = "terminals"
    template_name = "oscar/dashboard/stores/terminal_list.html"
    table_class = TerminalListTable
    
    def get_table_pagination(self, table):
        return dict(per_page=settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["queryset_description"] = self.description
        return ctx  

    def get_queryset(self):
        qs = Terminal._default_manager.prefetch_related("stores").annotate(store=F("stores"),).all()
        self.description = "Все платежные терминалы"
        return qs


class TerminalDetailView(DetailView):
    context_object_name = "terminal"
    model = Terminal
    template_name = "oscar/dashboard/stores/terminal_detail.html"

    def get(self, request, *args, **kwargs):
        """
        Ensures that the correct URL is used before rendering a response
        """
        # pylint: disable=attribute-defined-outside-init
        self.object = self.get_object()
        response = super().get(request, *args, **kwargs)
        return response

    def get_object(self, queryset=None):
        # Check if self.object is already set to prevent unnecessary DB calls
        if hasattr(self, "object"):
            return self.object
        else:
            return self._get_object(self.kwargs.get("pk"))


    def _get_object(self, terminal_id):
        return self.model.objects.get(id=terminal_id)



# =====
# Staff
# =====


class StaffListView(CustomerListView):
    context_table_name = "staffs"
    template_name = "oscar/dashboard/stores/staff_list.html"
    table_class = StaffListTable

    def get_queryset(self):
        self.search_filters = []
        queryset = Staff._default_manager.prefetch_related("user", "user__stores").all()
        return self.apply_search(queryset)

    def apply_search(self, queryset):
        # Set initial queryset description, used for template context
        self.desc_ctx = {
            "main_filter": "Все сотрудники",
            "phone_filter": "",
            "name_filter": "",
        }
        if self.form.is_valid():
            return self.apply_search_filters(queryset, self.form.cleaned_data)
        else:
            return queryset

    def get_table_pagination(self, table):
        return dict(per_page=settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE)

    def apply_search_filters(self, queryset, data):
        """
        Function is split out to allow customisation with little boilerplate.
        """
        if data["username"]:
            # username = data["username"]
            username = re.sub(r'[^\d+]', '', data["username"])
            queryset = queryset.filter(user__username__istartswith=username)
            self.desc_ctx["phone_filter"] = " с телефоном соответствующим '%s'" % username
            self.search_filters.append((('Телефон начинается с "%s"' % username), (("username", data["username"]),)))
        if data["name"]:
            # If the value is two words, then assume they are first name and
            # last name
            parts = data["name"].split()
            # always true filter
            condition = Q()
            for part in parts:
                condition |= (
                    Q(first_name__icontains=part) |
                    Q(last_name__icontains=part) |
                    Q(middle_name__icontains=part)
                )
            queryset = queryset.filter(condition).distinct()
            self.desc_ctx["name_filter"] = " с именем соответствующим '%s'" % data["name"]
            self.search_filters.append((('Имя соответствует "%s"' % data["name"]), (("name", data["name"]),)))

        return queryset

    def make_nothing(self, request, users):
        messages.info(self.request, "Выберите статус 'Активен' или 'Не активен'")
        return redirect("dashboard:staff-list")

    def _change_users_active_status(self, staffs, value):
        for staff in staffs:
            if not staff.user.is_superuser:
                staff.is_active = value
                staff.save()
        messages.info(self.request, "Cтатус персонала был успешно изменен")
        return redirect("dashboard:staff-list")


class StaffStatusView(UpdateView):
    model = Staff

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            staff_id = kwargs.get('pk')
            staff = self.model.objects.get(id=staff_id)
            staff.is_active = not staff.is_active
            staff.save()
            return self.get_success_url()
        except Exception:
            return self.get_error_url()

    def get_success_url(self):
        messages.info(self.request, "Статус сотрудника успешно изменен")
        return redirect("dashboard:staff-list")

    def get_error_url(self):
        messages.warning(self.request, "Статус сотрудника не был изменен")
        return redirect("dashboard:staff-list")


class StaffDetailView(UpdateView):
    model = Staff
    form_class = StaffForm
    template_name = "oscar/dashboard/stores/staff_detail.html"
    success_url = reverse_lazy('dashboard:staff-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # Добавляем request в kwargs
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Сотрудник успешно изменен!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при изменении группы. Проверьте введенные данные.')
        return super().form_invalid(form)


class StaffCreateView(CreateView):
    model = Staff
    form_class = StaffForm
    template_name = "oscar/dashboard/stores/staff_create.html"
    success_url = reverse_lazy('dashboard:staff-list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # Добавляем request в kwargs
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Сотрудник успешно создан!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при создании сотрудника. Проверьте введенные данные.')
        return super().form_invalid(form)


class StaffDeleteView(DeleteView):
    model = Staff
    template_name = "oscar/dashboard/stores/staff_delete.html"
    context_object_name = "staff"

    def get_success_url(self):
        messages.success(self.request, "Сотрудник успешно удален")
        return reverse("dashboard:staff-list")


# =============
# Store users
# =============


class StoreStaffCreateView(StaffCreateView):
    success_url = reverse_lazy('dashboard:store-list')

    def dispatch(self, request, *args, **kwargs):
        self.store = get_object_or_404(Store, pk=kwargs.get("store_pk", None))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["store"] = self.store
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["store"] = self.store
        return kwargs
    

class StoreStaffSelectView(StaffListView):
    template_name = "oscar/dashboard/stores/store_user_select.html"
    table_class = StoreStaffListTable

    def dispatch(self, request, *args, **kwargs):
        self.store = get_object_or_404(Store, pk=kwargs.get("store_pk", None))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["store"] = self.store
        ctx["form"] = self.form
        return ctx

    def get_queryset(self):
        self.search_filters = []
        store_exists = Store.objects.filter(users=OuterRef('user'), id=self.store.id)
        queryset = Staff._default_manager.prefetch_related("user", "user__stores").annotate(
            is_related_to_store=Exists(store_exists, output_field=BooleanField())
        ).all()
        return self.apply_search(queryset)


class StoreStaffLinkView(View):
    def get(self, request, user_pk, store_pk):
        # need to allow GET to make Undo link in StoreUserUnlinkView work
        return self.post(request, user_pk, store_pk)

    def post(self, request, user_pk, store_pk):
        user = get_object_or_404(User, pk=user_pk)
        name = user.get_full_name() or user.username
        store = get_object_or_404(Store, pk=store_pk)
        if self.link_user(user, store):
            messages.success(
                request,
                "Пользователь '%(name)s' был прикреплен к магазину - '%(store_name)s'"
                % {"name": name, "store_name": store.name},
            )
        else:
            messages.info(
                request,
                "Пользователь '%(name)s' уже прикреплен к магазину - '%(store_name)s'"
                % {"name": name, "store_name": store.name},
            )
        return redirect("dashboard:store-user-select", store_pk=store_pk)

    def link_user(self, user, store):
        """
        Links a user to a store, and adds the dashboard permission if needed.

        Returns False if the user was linked already; True otherwise.
        """
        if store.users.filter(pk=user.pk).exists():
            return False
        store.users.add(user)
        # if not user.is_staff:
            # dashboard_access_perm = Permission.objects.get(
            #     codename="dashboard_access", content_type__app_label="store"
            # )
            # user.user_permissions.add(dashboard_access_perm)
        return True


class StoreStaffUnlinkView(View):
    def unlink_user(self, user, store):
        """
        Unlinks a user from a store, and removes the dashboard permission
        if they are not linked to any other stores.

        Returns False if the user was not linked to the store; True
        otherwise.
        """
        if not store.users.filter(pk=user.pk).exists():
            return False
        store.users.remove(user)
        # if not user.is_staff and not user.stores.exists():
        #     dashboard_access_perm = Permission.objects.get(
        #         codename="dashboard_access", content_type__app_label="store"
        #     )
        #     user.user_permissions.remove(dashboard_access_perm)
        return True
    
    def get(self, request, user_pk, store_pk):
        # need to allow GET to make Undo link in StoreUserUnlinkView work
        return self.post(request, user_pk, store_pk)

    def post(self, request, user_pk, store_pk):
        user = get_object_or_404(User, pk=user_pk)
        name = user.get_full_name() or user.username
        store = get_object_or_404(Store, pk=store_pk)
        if self.unlink_user(user, store):
            msg = render_to_string(
                "oscar/dashboard/stores/messages/user_unlinked.html",
                {
                    "user_name": name,
                    "store_name": store.name,
                    "user_pk": user_pk,
                    "store_pk": store_pk,
                },
            )
            messages.success(self.request, msg, extra_tags="safe noicon")
        else:
            messages.error(
                request,
                "Пользователь '%(name)s' не прикреплен к магазину - '%(store_name)s'"
                % {"name": name, "store_name": store.name},
            )
        return redirect("dashboard:store-user-select", store_pk=store_pk)



# =====
# Groups
# =====


class GroupListView(SingleTableView):
    context_table_name = "groups"
    template_name = "oscar/dashboard/stores/group_list.html"
    table_class = GroupListTable

    def get_queryset(self):
        return Group._default_manager.prefetch_related("permissions", "evotor").all()

    def get_table_pagination(self, table):
        return dict(per_page=settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE)


class GroupDetailView(UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "oscar/dashboard/stores/group_detail.html"
    success_url = reverse_lazy('dashboard:group-list')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.get_object().name
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Группа успешно изменена!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при изменении группы. Проверьте введенные данные.')
        return super().form_invalid(form)


class GroupCreateView(CreateView):
    model = Group
    form_class = GroupForm
    template_name = "oscar/dashboard/stores/group_create.html"
    success_url = reverse_lazy('dashboard:group-list')
    # permission_required = 'auth.add_group'

    def form_valid(self, form):
        messages.success(self.request, 'Группа успешно создана!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при создании группы. Проверьте введенные данные.')
        return super().form_invalid(form)


class GroupDeleteView(DeleteView):
    model = Group
    template_name = "oscar/dashboard/stores/group_delete.html"
    context_object_name = "group"

    def get_success_url(self):
        messages.success(self.request, "Группы персонала успешно удалена")
        return reverse("dashboard:group-list")
