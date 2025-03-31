# pylint: disable=E1101
from urllib.parse import quote

from core.loading import get_class, get_model
from django.contrib import messages
from django.core.cache import cache
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect

BrowseCategoryForm = get_class("webshop.search.forms", "BrowseCategoryForm")
CategoryForm = get_class("webshop.search.forms", "CategoryForm")
BaseSearchView = get_class("webshop.search.views.base", "BaseSearchView")
PageTitleMixin = get_class("webshop.mixins", "PageTitleMixin")

Category = get_model("catalogue", "Category")


class CatalogueView(PageTitleMixin, BaseSearchView):
    """
    Browse all products in the catalogue
    """

    form_class = BrowseCategoryForm
    context_object_name = "products"
    template_name = "catalogue/browse.html"
    enforce_paths = True
    page_title = "Меню"

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            # Redirect to page one.
            messages.error(request, "Категория не найдена.")
            return redirect("catalogue:index")


class ProductCategoryView(PageTitleMixin, BaseSearchView):
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
        """Получает категорию из кеша или БД, используя slug из URL."""
        cache_key = f"category_{self.kwargs['category_slug']}"
        category = cache.get(cache_key)

        if category is None:
            slug = self.kwargs["category_slug"].split(Category._slug_separator)[-1]
            category = get_object_or_404(Category, slug=slug)
            cache.set(cache_key, category, timeout=3600)

        return category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["categories"] = self.category.get_descendants_and_self()
        return kwargs

    def get_page_title(self):
        return self.category.get_name()
