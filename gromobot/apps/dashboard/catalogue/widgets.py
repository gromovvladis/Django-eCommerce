from core.forms.widgets import MultipleRemoteSelect, RemoteSelect
from django.urls import reverse_lazy


class ProductSelect(RemoteSelect):
    # Implemented as separate class instead of just calling
    # AjaxSelect(data_url=...) for overridability and backwards compatibility
    lookup_url = reverse_lazy("dashboard:catalogue-product-lookup")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "select2 product-select"


class AdditionalSelect(RemoteSelect):
    # Implemented as separate class instead of just calling
    # AjaxSelect(data_url=...) for overridability and backwards compatibility
    lookup_url = reverse_lazy("dashboard:catalogue-additional-lookup")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "select2 product-select"


class AttributeSelect(RemoteSelect):
    # Implemented as separate class instead of just calling
    # AjaxSelect(data_url=...) for overridability and backwards compatibility
    lookup_url = reverse_lazy("dashboard:catalogue-attribute-lookup")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "select2 product-select"


class ProductSelectMultiple(MultipleRemoteSelect):
    # Implemented as separate class instead of just calling
    # AjaxSelect(data_url=...) for overridability and backwards compatibility
    lookup_url = reverse_lazy("dashboard:catalogue-product-lookup")
