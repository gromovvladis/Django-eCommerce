import logging

from oscar.apps.crm.client import EvatorCloud
logger = logging.getLogger("oscar.catalogue")

from django import forms
from django.core import exceptions
from django.forms.models import inlineformset_factory

from oscar.core.loading import get_classes, get_model

Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttribute = get_model("catalogue", "ProductAttribute")
StockRecord = get_model("store", "StockRecord")
ProductCategory = get_model("catalogue", "ProductCategory")
ProductImage = get_model("catalogue", "ProductImage")
ProductRecommendation = get_model("catalogue", "ProductRecommendation")
Additional = get_model("catalogue", "Additional")
ProductAdditional = get_model("catalogue", "ProductAdditional")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
AttributeOption = get_model("catalogue", "AttributeOption")

(
    StockRecordForm,
    StockRecordStockForm,
    ProductCategoryForm,
    ProductImageForm,
    ProductRecommendationForm,
    ProductAdditionalForm,
    ProductClassAdditionalForm,
    ProductAttributesForm,
    ProductClassAttributesForm,
    AttributeOptionForm,
) = get_classes(
    "dashboard.catalogue.forms",
    (
        "StockRecordForm",
        "StockRecordStockForm",
        "ProductCategoryForm",
        "ProductImageForm",
        "ProductRecommendationForm",
        "ProductAdditionalForm",
        "ProductClassAdditionalForm",
        "ProductAttributesForm",
        "ProductClassAttributesForm",
        "AttributeOptionForm",
    ),
)


BaseStockRecordFormSet = inlineformset_factory(
    Product, StockRecord, form=StockRecordForm, extra=1
)


class StockRecordFormSet(BaseStockRecordFormSet):
    def __init__(self, product_class, user, *args, **kwargs):
        self.user = user
        self.require_user_stockrecord = not user.is_staff
        self.product_class = product_class
        super().__init__(*args, **kwargs)
        self.set_initial_data()

    def set_initial_data(self):
        """
        If user has only one store associated, set the first
        stock record's store to it. Can't pre-select for staff users as
        they're allowed to save a product without a stock record.

        This is intentionally done after calling __init__ as passing initial
        data to __init__ creates a form for each list item. So depending on
        whether we can pre-select the store or not, we'd end up with 1 or 2
        forms for an unbound form.
        """
        if self.require_user_stockrecord:
            try:
                user_store = self.user.stores.get()
            except (exceptions.ObjectDoesNotExist, exceptions.MultipleObjectsReturned):
                pass
            else:
                store_field = self.forms[0].fields.get("store", None)
                if store_field and store_field.initial is None:
                    store_field.initial = user_store

    def _construct_form(self, i, **kwargs):
        kwargs["product_class"] = self.product_class
        kwargs["user"] = self.user
        return super()._construct_form(i, **kwargs)

    def clean(self):
        """
        If the user isn't a staff user, this validation ensures that at least
        one stock record's store is associated with a users stores.
        """
        if any(self.errors):
            return
        if self.require_user_stockrecord:
            stockrecord_stores = set(
                [form.cleaned_data.get("store", None) for form in self.forms]
            )
            user_stores = set(self.user.stores.all())
            if not user_stores & stockrecord_stores:
                raise exceptions.ValidationError("По крайней мере одна товарная запись должна быть установлена магазину, который связана с вами.")

    def update_evotor_stockrecord(self, product):
        try:
            product, error = EvatorCloud().update_evotor_stockrecord(product)
            return product, error
        except Exception as e:
            error = "Ошибка при отправке измененной товароной записи товара в Эвотор. Ошибка %s", e
            logger.error(error)
            return product, error



BaseStockRecordStockFormSet = inlineformset_factory(
    Product, StockRecord, form=StockRecordStockForm, extra=0
)


class StockRecordStockFormSet(BaseStockRecordStockFormSet):
    def __init__(self, product_class, user, *args, **kwargs):
        self.user = user
        self.require_user_stockrecord = not user.is_staff
        self.product_class = product_class

        super().__init__(*args, **kwargs)
        self.set_initial_data()

    def set_initial_data(self):
        """
        If user has only one store associated, set the first
        stock record's store to it. Can't pre-select for staff users as
        they're allowed to save a product without a stock record.

        This is intentionally done after calling __init__ as passing initial
        data to __init__ creates a form for each list item. So depending on
        whether we can pre-select the store or not, we'd end up with 1 or 2
        forms for an unbound form.
        """
        if self.require_user_stockrecord:
            try:
                user_store = self.user.stores.get()
            except (exceptions.ObjectDoesNotExist, exceptions.MultipleObjectsReturned):
                pass
            else:
                store_field = self.forms[0].fields.get("store", None)
                if store_field and store_field.initial is None:
                    store_field.initial = user_store

    def _construct_form(self, i, **kwargs):
        kwargs["product_class"] = self.product_class
        kwargs["user"] = self.user
        return super()._construct_form(i, **kwargs)

    def clean(self):
        """
        If the user isn't a staff user, this validation ensures that at least
        one stock record's store is associated with a users stores.
        """
        if any(self.errors):
            return
        if self.require_user_stockrecord:
            stockrecord_stores = set(
                [form.cleaned_data.get("store", None) for form in self.forms]
            )
            user_stores = set(self.user.stores.all())
            if not user_stores & stockrecord_stores:
                raise exceptions.ValidationError("По крайней мере одна товарная запись должна быть установлена магазину, который связана с вами.")


BaseProductCategoryFormSet = inlineformset_factory(
    Product, ProductCategory, form=ProductCategoryForm, extra=1, can_delete=True
)


class ProductCategoryFormSet(BaseProductCategoryFormSet):
    # pylint: disable=unused-argument
    def __init__(self, product_class, user, *args, **kwargs):
        # This function just exists to drop the extra arguments
        super().__init__(*args, **kwargs)

    def clean(self):
        if not self.instance.is_child and self.get_num_categories() == 0:
            raise forms.ValidationError(
                "товары должны иметь хотя бы одну категорию."
            )
        if self.instance.is_child and self.get_num_categories() > 0:
            raise forms.ValidationError("Дочерний товар не должен иметь категорий")

    def get_num_categories(self):
        num_categories = 0
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if (
                hasattr(form, "cleaned_data")
                and form.cleaned_data.get("category", None)
                and not form.cleaned_data.get("DELETE", False)
            ):
                num_categories += 1
        return num_categories


BaseProductImageFormSet = inlineformset_factory(
    Product, ProductImage, form=ProductImageForm, extra=1
)


class ProductImageFormSet(BaseProductImageFormSet):
    # pylint: disable=unused-argument
    def __init__(self, product_class, user, *args, **kwargs):
        super().__init__(*args, **kwargs)


BaseProductRecommendationFormSet = inlineformset_factory(
    Product,
    ProductRecommendation,
    form=ProductRecommendationForm,
    extra=6,
    fk_name="primary",
)


class ProductRecommendationFormSet(BaseProductRecommendationFormSet):
    # pylint: disable=unused-argument
    def __init__(self, product_class, user, *args, **kwargs):
        super().__init__(*args, **kwargs)


BaseProductAdditionalFormSet = inlineformset_factory(
    Product,
    ProductAdditional,
    form=ProductAdditionalForm,
    extra=6,
    fk_name="primary_product",
)

class ProductAdditionalFormSet(BaseProductAdditionalFormSet):
    # pylint: disable=unused-argument
    def __init__(self, product_class, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            product_id = kwargs.get("instance").id 
            for form in self.forms:
                form.fields["additional_product"].widget.attrs["data-product-id"] = product_id 
                form.fields["additional_product"].widget.attrs["data-class-id"] = product_class.id 
        except AttributeError:
            pass


BaseProductClassAdditionalFormSet = inlineformset_factory(
    ProductClass,
    ProductAdditional,
    form=ProductClassAdditionalForm,
    extra=3,
    fk_name="primary_class",
)


class ProductClassAdditionalFormSet(BaseProductClassAdditionalFormSet):
    # pylint: disable=unused-argument
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


BaseProductAttributeFormSet = inlineformset_factory(
    Product, 
    ProductAttribute, 
    form=ProductAttributesForm, 
    extra=3,
    fk_name="product",
    # can_delete=False,
)


class ProductAttributeFormSet(BaseProductAttributeFormSet):
    def __init__(self, product_class, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            product_id = kwargs.get("instance").id 
            for form in self.forms:
                form.fields["attribute"].widget.attrs["data-product-id"] = product_id 
                form.fields["attribute"].widget.attrs["data-class-id"] = product_class.id 
        except AttributeError:
            pass


BaseProductClassAttributeFormSet = inlineformset_factory(
    ProductClass, 
    ProductAttribute, 
    form=ProductClassAttributesForm, 
    extra=3,
    fk_name="product_class",
)


class ProductClassAttributeFormSet(BaseProductClassAttributeFormSet):
    # pylint: disable=unused-argument
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


AttributeOptionFormSet = inlineformset_factory(
    AttributeOptionGroup, AttributeOption, form=AttributeOptionForm, extra=6
)
