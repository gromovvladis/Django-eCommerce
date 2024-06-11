from oscar.core.loading import get_class

FacetedSearchView = get_class("search.views.search", "FacetedSearchView")
SearchView = get_class("search.views.search", "SearchView")
CatalogueView = get_class("search.views.catalogue", "CatalogueView")
ProductCategoryView = get_class("search.views.catalogue", "ProductCategoryView")
