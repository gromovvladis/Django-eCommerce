from core.application import Config
from core.loading import get_class
from django.urls import path


class SearchConfig(Config):
    label = "search"
    name = "apps.webshop.search"
    verbose_name = "Поиск"

    namespace = "search"

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.search_result_view = get_class("webshop.search.views", "FacetedSearchView")
        self.search_view = get_class("webshop.search.views", "SearchView")
        self.suggestions_view = get_class("webshop.search.views.search", "SuggestionsView")

    def get_urls(self):
        urlpatterns = [
            path(
                "api/suggestions/", self.suggestions_view.as_view(), name="suggestions"
            ),
            path("result/", self.search_result_view.as_view(), name="search"),
            path("", self.search_view.as_view(), name="search-page"),
        ]

        return self.post_process_urls(urlpatterns)
