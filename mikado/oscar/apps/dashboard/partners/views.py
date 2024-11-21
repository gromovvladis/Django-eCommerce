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
Partner = get_model("partner", "Partner")
Terminal = get_model("partner", "Terminal")
(
    PartnerSearchForm,
    PartnerForm,
) = get_classes(
    "dashboard.partners.forms",
    [
        "PartnerSearchForm",
        "PartnerForm",
    ],
)
StaffForm = get_class("dashboard.users.forms","StaffForm")
GroupForm = get_class("dashboard.users.forms","GroupForm")
PartnerListTable = get_class("dashboard.partners.tables", "PartnerListTable")
GroupListTable = get_class("dashboard.partners.tables", "GroupListTable")
StaffListTable = get_class("dashboard.partners.tables", "StaffListTable")
TerminalListTable = get_class("dashboard.partners.tables", "TerminalListTable")
PartnerStaffListTable = get_class("dashboard.partners.tables", "PartnerStaffListTable")


class PartnerListView(SingleTableView):
    context_table_name = "partners"
    template_name = "oscar/dashboard/partners/partner_list.html"
    form_class = PartnerSearchForm
    table_class = PartnerListTable

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
        qs = Partner._default_manager.prefetch_related("addresses", "users", "users__profile").all()

        self.description = "Все точки продаж"

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


class PartnerCreateView(CreateView):
    model = Partner
    template_name = "oscar/dashboard/partners/partner_form.html"
    form_class = PartnerForm
    success_url = reverse_lazy("dashboard:partner-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Создать точку продажи"
        return ctx

    def get_success_url(self):
        messages.success(
            self.request, "Точка продажи '%s' успешно создана. Доступно добавление персонала." % self.object.name
        )
        # Используем reverse для получения строки URL
        return reverse("dashboard:partner-manage", kwargs={"pk": self.object.id})
        
    def form_valid(self, form):
        self.object = form.save()
        self.object.address = self.object.addresses.model(partner=self.object)
        self.object.address.line1 = form.cleaned_data["line1"]
        self.object.address.coords_long = form.cleaned_data["coords_long"]
        self.object.address.coords_lat = form.cleaned_data["coords_lat"]
        self.object.address.save()
        return super().form_valid(form)


class PartnerManageView(UpdateView):
    """
    This multi-purpose view renders out a form to edit the partner's details,
    the associated address and a list of all associated users.
    """
    model = Partner
    template_name = "oscar/dashboard/partners/partner_manage.html"
    form_class = PartnerForm
    success_url = reverse_lazy("dashboard:partner-list")

    def get_object(self, queryset=None):
        self.partner = get_object_or_404(Partner, pk=self.kwargs["pk"])
        self.address = self.partner.primary_address
        if self.address is None:
            self.address = self.partner.addresses.model(partner=self.partner)
        return self.partner

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["partner"] = self.partner
        ctx["title"] = self.partner.name
        ctx["users"] = self.partner.users.all()
        ctx["terminals"] = self.partner.terminals.all()
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
            "Точка продажи '%s' успешно обновлена." % self.object.name,
        )
        return super().form_valid(form)


class PartnerDeleteView(DeleteView):
    model = Partner
    template_name = "oscar/dashboard/partners/partner_delete.html"

    def get_success_url(self):
        messages.success(
            self.request, "Точка продажи '%s' успешно удалена." % self.object.name
        )
        return reverse("dashboard:partner-list")



# =====
# Terminals
# =====


class TerminalListView(SingleTableView):
    context_table_name = "terminals"
    template_name = "oscar/dashboard/partners/terminal_list.html"
    table_class = TerminalListTable
    
    def get_table_pagination(self, table):
        return dict(per_page=settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["queryset_description"] = self.description
        return ctx  

    def get_queryset(self):
        qs = Terminal._default_manager.prefetch_related("partners").annotate(partner=F("partners"),).all()
        self.description = "Все платежные терминалы"
        return qs


class TerminalDetailView(DetailView):
    context_object_name = "terminal"
    model = Terminal
    template_name = "oscar/dashboard/partners/terminal_detail.html"

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
    template_name = "oscar/dashboard/partners/staff_list.html"
    table_class = StaffListTable

    def get_queryset(self):
        self.search_filters = []
        queryset = Staff._default_manager.prefetch_related("user", "user__partners").all()
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
    template_name = "oscar/dashboard/partners/staff_detail.html"
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
    template_name = "oscar/dashboard/partners/staff_create.html"
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
    template_name = "oscar/dashboard/partners/staff_delete.html"
    context_object_name = "staff"

    def get_success_url(self):
        messages.success(self.request, "Сотрудник успешно удален")
        return reverse("dashboard:staff-list")


# =============
# Partner users
# =============


class PartnerStaffCreateView(StaffCreateView):
    success_url = reverse_lazy('dashboard:partner-list')

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(Partner, pk=kwargs.get("partner_pk", None))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["partner"] = self.partner
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["partner"] = self.partner
        return kwargs
    

class PartnerStaffSelectView(StaffListView):
    template_name = "oscar/dashboard/partners/partner_user_select.html"
    table_class = PartnerStaffListTable

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(Partner, pk=kwargs.get("partner_pk", None))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["partner"] = self.partner
        ctx["form"] = self.form
        return ctx

    def get_queryset(self):
        self.search_filters = []
        partner_exists = Partner.objects.filter(users=OuterRef('user'), id=self.partner.id)
        queryset = Staff._default_manager.prefetch_related("user", "user__partners").annotate(
            is_related_to_partner=Exists(partner_exists, output_field=BooleanField())
        ).all()
        return self.apply_search(queryset)


class PartnerStaffLinkView(View):
    def get(self, request, user_pk, partner_pk):
        # need to allow GET to make Undo link in PartnerUserUnlinkView work
        return self.post(request, user_pk, partner_pk)

    def post(self, request, user_pk, partner_pk):
        user = get_object_or_404(User, pk=user_pk)
        name = user.get_full_name() or user.username
        partner = get_object_or_404(Partner, pk=partner_pk)
        if self.link_user(user, partner):
            messages.success(
                request,
                "Пользователь '%(name)s' был прикреплен к точке продаж - '%(partner_name)s'"
                % {"name": name, "partner_name": partner.name},
            )
        else:
            messages.info(
                request,
                "Пользователь '%(name)s' уже прикреплен к точке продаж - '%(partner_name)s'"
                % {"name": name, "partner_name": partner.name},
            )
        return redirect("dashboard:partner-user-select", partner_pk=partner_pk)

    def link_user(self, user, partner):
        """
        Links a user to a partner, and adds the dashboard permission if needed.

        Returns False if the user was linked already; True otherwise.
        """
        if partner.users.filter(pk=user.pk).exists():
            return False
        partner.users.add(user)
        # if not user.is_staff:
            # dashboard_access_perm = Permission.objects.get(
            #     codename="dashboard_access", content_type__app_label="partner"
            # )
            # user.user_permissions.add(dashboard_access_perm)
        return True


class PartnerStaffUnlinkView(View):
    def unlink_user(self, user, partner):
        """
        Unlinks a user from a partner, and removes the dashboard permission
        if they are not linked to any other partners.

        Returns False if the user was not linked to the partner; True
        otherwise.
        """
        if not partner.users.filter(pk=user.pk).exists():
            return False
        partner.users.remove(user)
        # if not user.is_staff and not user.partners.exists():
        #     dashboard_access_perm = Permission.objects.get(
        #         codename="dashboard_access", content_type__app_label="partner"
        #     )
        #     user.user_permissions.remove(dashboard_access_perm)
        return True
    
    def get(self, request, user_pk, partner_pk):
        # need to allow GET to make Undo link in PartnerUserUnlinkView work
        return self.post(request, user_pk, partner_pk)

    def post(self, request, user_pk, partner_pk):
        user = get_object_or_404(User, pk=user_pk)
        name = user.get_full_name() or user.username
        partner = get_object_or_404(Partner, pk=partner_pk)
        if self.unlink_user(user, partner):
            msg = render_to_string(
                "oscar/dashboard/partners/messages/user_unlinked.html",
                {
                    "user_name": name,
                    "partner_name": partner.name,
                    "user_pk": user_pk,
                    "partner_pk": partner_pk,
                },
            )
            messages.success(self.request, msg, extra_tags="safe noicon")
        else:
            messages.error(
                request,
                "Пользователь '%(name)s' не прикреплен к точке продаж - '%(partner_name)s'"
                % {"name": name, "partner_name": partner.name},
            )
        return redirect("dashboard:partner-user-select", partner_pk=partner_pk)



# =====
# Groups
# =====


class GroupListView(SingleTableView):
    context_table_name = "groups"
    template_name = "oscar/dashboard/partners/group_list.html"
    table_class = GroupListTable

    def get_queryset(self):
        return Group._default_manager.prefetch_related("permissions", "evotor").all()

    def get_table_pagination(self, table):
        return dict(per_page=settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE)


class GroupDetailView(UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "oscar/dashboard/partners/group_detail.html"
    success_url = reverse_lazy('dashboard:group-list')
    # permission_required = 'auth.add_group'


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
    template_name = "oscar/dashboard/partners/group_create.html"
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
    template_name = "oscar/dashboard/partners/group_delete.html"
    context_object_name = "group"

    def get_success_url(self):
        messages.success(self.request, "Группы персонала успешно удалена")
        return reverse("dashboard:group-list")
