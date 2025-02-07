from django.urls import path

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class SearchConfig(OscarConfig):
    label = "search"
    name = "oscar.apps.search"
    verbose_name = "Поиск"

    namespace = "search"

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.search_result_view = get_class("search.views", "FacetedSearchView")
        self.search_view = get_class("search.views", "SearchView")
        self.suggestions_view = get_class("search.views.search", "SuggestionsView")

    def get_urls(self):
        urlpatterns = [
            path(
                "api/suggestions/", self.suggestions_view.as_view(), name="suggestions"
            ),
            path("result/", self.search_result_view.as_view(), name="search"),
            path("", self.search_view.as_view(), name="search-page"),
        ]

        return self.post_process_urls(urlpatterns)
