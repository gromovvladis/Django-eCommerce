from haystack import indexes

from oscar.core.loading import get_class, get_model

# Load default strategy (without a user/request)
# is_solr_supported = get_class("search.features", "is_solr_supported")

Selector = get_class("store.strategy", "Selector")


class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    # Search text
    text = indexes.CharField(
        document=True,
        use_template=True,
        template_name="oscar/search/indexes/product/item_text.txt",
    )

    upc = indexes.CharField(model_attr="upc", null=True)
    title = indexes.EdgeNgramField(model_attr="title", null=True)
    title_exact = indexes.CharField(model_attr="title", null=True, indexed=False)

    # Fields for faceting
    product_class = indexes.CharField(null=True, faceted=False)
    category = indexes.MultiValueField(null=True, faceted=True)
    category_name = indexes.CharField(null=True, indexed=False)

    is_available = indexes.BooleanField(null=True, faceted=True)
    order = indexes.IntegerField(model_attr="order", null=True, faceted=False) 
    short_description = indexes.CharField(model_attr="short_description", null=True, faceted=False)

    # Spelling suggestions
    suggestions = indexes.FacetCharField()

    # date_created = indexes.DateTimeField(model_attr="date_created")
    date_updated = indexes.DateTimeField(model_attr="date_updated")

    is_public = indexes.BooleanField(model_attr="is_public")
    structure = indexes.CharField(model_attr="structure")

    _strategy = None

    def get_model(self):
        return get_model("catalogue", "Product")

    def index_queryset(self, using=None):
        # Only index browsable products (not each individual child product)
        # return self.get_model().objects.browsable().order_by("-order")
        return self.get_model().objects.browsable()

    def read_queryset(self, using=None):
        return self.get_model().objects.browsable().base_queryset()

    def prepare_product_class(self, obj):
        return obj.get_product_class().name

    def prepare_category(self, obj):
        return list(obj.get_categories().values_list("pk", flat=True)) or []

    def prepare_category_name(self, obj):
        return " ".join(obj.get_categories().values_list("name", flat=True) or [])
    
    def prepare_is_available(self, obj):
        strategy = self.get_strategy()
        return strategy.is_available(obj)

    # Pricing and stock is tricky as it can vary per customer.  However, the
    # most common case is for customers to see the same prices and stock levels
    # and so we implement that case here.

    def get_strategy(self):
        if not self._strategy:
            self._strategy = Selector().strategy()
        return self._strategy

    def prepare(self, obj):
        prepared_data = super().prepare(obj)
        # Use title for spelling suggestions
        # prepared_data["suggestions"] = prepared_data["title"]
        prepared_data["suggestions"] = (
            prepared_data.get("title", ""),
            prepared_data.get("short_description", ""),
            prepared_data.get("category_name", ""),
        )

        return prepared_data

    def get_updated_field(self):
        """
        Used to specify the field used to determine if an object has been
        updated

        Can be used to filter the query set when updating the index
        """
        return "date_updated"
