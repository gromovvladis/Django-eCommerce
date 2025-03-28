from core.loading import get_class

FacetedSearchView = get_class("webshop.search.views.search", "FacetedSearchView")
SearchView = get_class("webshop.search.views.search", "SearchView")
CatalogueView = get_class("webshop.search.views.catalogue", "CatalogueView")
ProductCategoryView = get_class("webshop.search.views.catalogue", "ProductCategoryView")
