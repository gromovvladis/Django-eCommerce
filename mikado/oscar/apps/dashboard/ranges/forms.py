import re
from django import forms
from django.db.models import Q

from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")
Range = get_model("offer", "Range")
RangeProductFileUpload = get_model("offer", "RangeProductFileUpload")

UPC_SET_REGEX = re.compile(r"[^,\s]+")


class RangeForm(forms.ModelForm):
    class Meta:
        model = Range
        fields = [
            "name",
            "description",
            "is_public",
            "includes_all_products",
            "included_categories",
        ]


# pylint: disable=attribute-defined-outside-init
class RangeProductForm(forms.Form):
    query = forms.CharField(
        max_length=1024,
        label="Артикулы товара или UPC",
        widget=forms.Textarea,
        required=False,
        help_text="Вы можете вставить выбранные SKU или UPC",
    )
    file_upload = forms.FileField(
        label="Файл SKU или UPC",
        required=False,
        max_length=255,
        help_text="Либо через запятую, либо по одному идентификатору в строке",
    )
    upload_type = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, product_range, *args, **kwargs):
        self.product_range = product_range
        super().__init__(*args, **kwargs)

    def clean_query_with_upload_type(self, raw, upload_type):
        # Check that the search matches some products
        ids = set(UPC_SET_REGEX.findall(raw))
        # switch for included or excluded products
        if upload_type == RangeProductFileUpload.EXCLUDED_PRODUCTS_TYPE:
            products = self.product_range.excluded_products.all()
            action = "исключено из этого диапазона"
        else:
            products = self.product_range.all_products()
            action = "добавлено в этот диапазон"
        existing_skus = set(
            products.values_list("stockrecords__evotor_code", flat=True)
        )
        existing_upcs = set(products.values_list("upc", flat=True))
        existing_ids = existing_skus.union(existing_upcs)
        new_ids = ids - existing_ids
        if len(new_ids) == 0:
            self.add_error(
                "query",
                (
                    "К товарам с номерами SKU или UPC, соответствующими %(skus)s, "
                    "уже было применено %(action)s"
                )
                % {"skus": ", ".join(ids), "action": action},
            )
        else:
            self.products = Product._default_manager.filter(
                Q(stockrecords__evotor_code__in=new_ids) | Q(upc__in=new_ids)
            )
            if len(self.products) == 0:
                self.add_error(
                    "query",
                    "Нет товаров, соответствующих SKU или UPC %s"
                    % ", ".join(ids),
                )
            found_skus = set(
                self.products.values_list("stockrecords__evotor_code", flat=True)
            )
            found_upcs = set(self.products.values_list("upc", flat=True))
            found_ids = found_skus.union(found_upcs)
            self.missing_skus = new_ids - found_ids
            self.duplicate_skus = existing_ids.intersection(ids)

    def clean(self):
        clean_data = super().clean()
        if not clean_data.get("query") and not clean_data.get("file_upload"):
            raise forms.ValidationError("Вы должны отправить либо список SKU/UPC, либо файл.")

        raw = clean_data["query"]
        if raw:
            self.clean_query_with_upload_type(raw, clean_data["upload_type"])
        return clean_data

    def get_products(self):
        return self.products if hasattr(self, "products") else []

    def get_missing_skus(self):
        return self.missing_skus

    def get_duplicate_skus(self):
        return self.duplicate_skus


# pylint: disable=attribute-defined-outside-init
class RangeExcludedProductForm(RangeProductForm):
    """
    Form to add products in range.excluded_products
    """

    def clean_query(self):
        raw = self.cleaned_data["query"]
        if not raw:
            return raw

        # Check that the search matches some products
        ids = set(UPC_SET_REGEX.findall(raw))
        products = self.product_range.excluded_products.all()
        existing_skus = set(
            products.values_list("stockrecords__evotor_code", flat=True)
        )
        existing_upcs = set(products.values_list("upc", flat=True))
        existing_ids = existing_skus.union(existing_upcs)
        new_ids = ids - existing_ids

        if len(new_ids) == 0:
            raise forms.ValidationError(
                "Товары с номерами SKU или UPC, соответствующими %s, уже находятся в этом ассортименте"
                % (", ".join(ids))
            )

        self.products = Product._default_manager.filter(
            Q(stockrecords__evotor_code__in=new_ids) | Q(upc__in=new_ids)
        )
        if len(self.products) == 0:
            raise forms.ValidationError("Нет товаров, соответствующих SKU или UPC %s") % ", ".join(ids)

        found_skus = set(
            self.products.values_list("stockrecords__evotor_code", flat=True)
        )
        found_upcs = set(self.products.values_list("upc", flat=True))
        found_ids = found_skus.union(found_upcs)
        self.missing_skus = new_ids - found_ids
        self.duplicate_skus = existing_ids.intersection(ids)

        return raw
