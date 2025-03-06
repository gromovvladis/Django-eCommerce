from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import generic
from django_tables2 import SingleTableView

from oscar.core.loading import get_class, get_classes, get_model
from oscar.core.utils import slugify
from oscar.core.validators import URLDoesNotExistValidator

PageSearchForm, PageUpdateForm = get_classes(
    "dashboard.pages.forms", ("PageSearchForm", "PageUpdateForm")
)

FlatPage = get_model("flatpages", "FlatPage")
Site = get_model("sites", "Site")

PagesTable = get_class("dashboard.pages.tables", "PagesTable")


class PageListView(SingleTableView):
    """
    View for listing all existing flatpages.
    """

    template_name = "oscar/dashboard/pages/pages_list.html"
    model = FlatPage
    form_class = PageSearchForm
    table_class = PagesTable
    context_table_name = "flatpages"
    desc_template = "%(main_filter)s %(title_filter)s"

    def get_table_pagination(self, table):
        return dict(per_page=settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE)

    def get_queryset(self):
        """
        Get queryset of all flatpages to be displayed. If a
        search term is specified in the search form, it will be used
        to filter the queryset.
        """
        # pylint: disable=attribute-defined-outside-init
        self.desc_ctx = {
            "main_filter": "Все станицы",
            "title_filter": "",
        }
        queryset = self.model.objects.all().order_by("title")

        # pylint: disable=attribute-defined-outside-init
        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data["title"]:
            queryset = queryset.filter(title__icontains=data["title"])
            self.desc_ctx["title_filter"] = (
                " с заголовком, содержащим '%s'" % data["title"]
            )

        return queryset

    def get_context_data(self, **kwargs):
        """
        Get context data with *form* and *queryset_description* data
        added to it.
        """
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["queryset_description"] = self.desc_template % self.desc_ctx
        return context

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        if self.form.is_valid():
            table.caption = "Результаты поиска: %s" % self.object_list.count()

        return table


class PageCreateUpdateMixin(object):
    template_name = "oscar/dashboard/pages/update.html"
    model = FlatPage
    form_class = PageUpdateForm
    context_object_name = "page"

    def get_success_url(self):
        msg = render_to_string(
            "oscar/dashboard/pages/messages/saved.html", {"page": self.object}
        )
        messages.success(self.request, msg, extra_tags="safe noicon")
        return reverse("dashboard:page-list")

    def form_valid(self, form):
        # Ensure saved page is added to the current site
        page = form.save()
        if not page.sites.exists():
            page.sites.add(Site.objects.get_current())
        self.object = page
        return HttpResponseRedirect(self.get_success_url())


class PageCreateView(PageCreateUpdateMixin, generic.CreateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Создать новую страницу"
        return ctx

    def form_valid(self, form):
        """
        Store new flatpage from form data.
        Additionally, if URL is left blank, a slugified
        version of the title will be used as URL after checking
        if it is valid.
        """
        # if no URL is specified, generate from title
        page = form.save(commit=False)

        if not page.url:
            page.url = "/%s/" % slugify(page.title)

        try:
            URLDoesNotExistValidator()(page.url)
        except ValidationError:
            pass
        else:
            return super().form_valid(form)

        ctx = self.get_context_data()
        ctx["form"] = form
        return self.render_to_response(ctx)


class PageUpdateView(PageCreateUpdateMixin, generic.UpdateView):
    """
    View for updating flatpages from the dashboard.
    """

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = self.object.title
        return ctx


class PageDeleteView(generic.DeleteView):
    template_name = "oscar/dashboard/pages/delete.html"
    context_object_name = "page"
    model = FlatPage

    def get_success_url(self):
        messages.success(self.request, "Удалить страницу '%s'." % self.object.title)
        return reverse("dashboard:page-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = self.object.title
        return ctx
