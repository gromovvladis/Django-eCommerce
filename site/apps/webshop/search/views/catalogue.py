# pylint: disable=E1101
from urllib.parse import quote

from django.contrib import messages
from django.core.cache import cache
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect
from core.loading import get_class, get_model

BrowseCategoryForm = get_class("webshop.search.forms", "BrowseCategoryForm")
CategoryForm = get_class("webshop.search.forms", "CategoryForm")
BaseSearchView = get_class("webshop.search.views.base", "BaseSearchView")

Category = get_model("catalogue", "Category")


class CatalogueView(BaseSearchView):
    """
    Browse all products in the catalogue
    """
    form_class = BrowseCategoryForm
    context_object_name = "products"
    template_name = "catalogue/browse.html"
    enforce_paths = True

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            # Redirect to page one.
            messages.error(request, "Категория не найдена.")
            return redirect("catalogue:index")

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["page_title"] = "Меню"
        return ctx


class ProductCategoryView(BaseSearchView):
    """
    Browse products in a given category
    """
    form_class = CategoryForm
    enforce_paths = True
    context_object_name = "products"
    template_name = "catalogue/category.html"

    def get(self, request, *args, **kwargs):
        # pylint: disable=W0201
        self.category = self.get_category()

        # Allow staff members so they can test layout etc.
        if not self.is_viewable(self.category, request):
            raise Http404()

        potential_redirect = self.redirect_if_necessary(request.path, self.category)
        if potential_redirect is not None:
            return potential_redirect

        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            messages.error(request, "Категория не найдена.")
            return redirect(self.category.get_absolute_url())

    def is_viewable(self, category, request):
        return category.is_public or request.user.is_staff

    def redirect_if_necessary(self, current_path, category):
        if self.enforce_paths:
            # Categories are fetched by primary key to allow slug changes.
            # If the slug has changed, issue a redirect.
            expected_path = category.get_absolute_url()
            if expected_path != quote(current_path):
                return HttpResponsePermanentRedirect(expected_path)

    def get_category(self):
        category = cache.get("category_%s" % self.kwargs["category_slug"])

        if not category:
            # category = get_object_or_404(Category, slug=self.kwargs["category_slug"])
            # slug = self.kwargs["category_slug"].split(Category._slug_separator)
            slug = self.kwargs["category_slug"].split(Category._slug_separator)[-1]
            category = get_object_or_404(Category, slug=slug)
            cache.set("category_%s" % self.kwargs["category_slug"], category, 3600)

        return category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        context["page_title"] = self.category.get_name()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["categories"] = self.category.get_descendants_and_self()
        return kwargs
