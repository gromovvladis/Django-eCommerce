from core.loading import get_class
from django.conf import settings
from haystack.generic_views import FacetedSearchView as BaseFacetedSearchView

base_sqs = get_class("webshop.search.facets", "base_sqs")


class BaseSearchView(BaseFacetedSearchView):
    paginate_by = settings.PRODUCTS_PER_PAGE

    def get_queryset(self):
        return base_sqs()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        form = context[self.form_name]

        # Show suggestion no matter what.  Haystack 2.1 only shows a suggestion
        # if there are some results, which seems a bit weird to me.
        if self.queryset.query.backend.include_spelling:
            # Note, this triggers an extra call to the search backend
            suggestion = form.get_suggestion()
            if suggestion != context["query"]:
                context["suggestion"] = suggestion

        return context
