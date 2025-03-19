from collections import defaultdict

from django import forms
from django.forms.widgets import Input
from haystack.forms import FacetedSearchForm
from core.loading import get_class

is_solr_supported = get_class("webshop.search.features", "is_solr_supported")


class SearchInput(Input):
    """
    Defining a search type widget

    This is an HTML5 thing and works nicely with Safari, other browsers default
    back to using the default "text" type
    """

    input_type = "search"


class SearchForm(FacetedSearchForm):
    """
    In Haystack, the search form is used for interpreting
    and sub-filtering the SQS.
    """

    # Use a tabindex of 1 so that users can hit tab on any page and it will
    # focus on the search widget.
    q = forms.CharField(
        required=False,
        label="Поиск",
        widget=SearchInput(
            {"placeholder": "Поиск", "tabindex": "1", "class": "form-control"}
        ),
    )

    # Search
    RELEVANCY = "relevancy"
    TOP_RATED = "rating"
    NEWEST = "newest"
    PRICE_HIGH_TO_LOW = "price-desc"
    PRICE_LOW_TO_HIGH = "price-asc"
    NAME_A_TO_Z = "name-asc"
    NAME_Z_TO_A = "name-desc"

    SORT_BY_CHOICES = [
        (RELEVANCY, "Релевантность"),
        (TOP_RATED, "Оценка пользователя"),
        (NEWEST, "Наиболее новые"),
        (PRICE_HIGH_TO_LOW, "Цена | От большей к меньшей"),
        (PRICE_LOW_TO_HIGH, "Цена | От меньшей к большей"),
        (NAME_A_TO_Z, "Название от А до Я"),
        (NAME_Z_TO_A, "Название от Я до А"),
    ]

    # Map query params to sorting fields.  Note relevancy isn't included here
    # as we assume results are returned in relevancy order in the absence of an
    # explicit sort field being passed to the search backend.
    SORT_BY_MAP = {
        TOP_RATED: "-rating",
        NEWEST: "-date_created",
        PRICE_HIGH_TO_LOW: "-price",
        PRICE_LOW_TO_HIGH: "price",
        NAME_A_TO_Z: "name_s",
        NAME_Z_TO_A: "-name_s",
    }
    # Non Solr backends don't support dynamic fields so we just sort on name
    if not is_solr_supported():
        SORT_BY_MAP[NAME_A_TO_Z] = "name_exact"
        SORT_BY_MAP[NAME_Z_TO_A] = "-name_exact"

    sort_by = forms.ChoiceField(
        label="Сортировать по",
        choices=SORT_BY_CHOICES,
        widget=forms.Select(),
        required=False,
    )

    @property
    def selected_multi_facets(self):
        """
        Validate and return the selected facets
        """
        # Process selected facets into a dict(field->[*values]) to handle
        # multi-faceting
        selected_multi_facets = defaultdict(list)

        for facet_kv in self.selected_facets:
            if ":" not in facet_kv:
                continue
            field_name, value = facet_kv.split(":", 1)

            selected_multi_facets[field_name].append(value)

        return selected_multi_facets

    def search(self):
        # We replace the 'search' method from FacetedSearchForm, so that we can
        # handle range queries
        # Note, we call super on a parent class as the default faceted view
        # escapes everything (which doesn't work for price range queries)
        sqs = super(FacetedSearchForm, self).search()

        # We need to process each facet to ensure that the field name and the
        # value are quoted correctly and separately:
        for field, values in self.selected_multi_facets.items():
            if not values:
                continue
            else:
                # Field facet - clean and quote the values
                clean_values = ['"%s"' % sqs.query.clean(val) for val in values]
                sqs = sqs.narrow("%s:(%s)" % (field, " OR ".join(clean_values)))

        if self.is_valid() and "sort_by" in self.cleaned_data:
            sort_field = self.SORT_BY_MAP.get(self.cleaned_data["sort_by"], None)
            if sort_field:
                sqs = sqs.order_by(sort_field)

        return sqs


class BrowseCategoryForm(SearchForm):
    """
    Variant of SearchForm that returns all products (instead of none) if no
    query is specified.
    """

    def no_query_found(self):
        """
        Return Queryset of all the results.
        """
        return self.searchqueryset


class CategoryForm(BrowseCategoryForm):
    def __init__(self, categories, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.categories = categories

    def no_query_found(self):
        """
        Return Queryset of all the results.
        """
        sqs = super().no_query_found()

        category_ids = list(self.categories.values_list("pk", flat=True))
        return sqs.filter(category__in=category_ids)
