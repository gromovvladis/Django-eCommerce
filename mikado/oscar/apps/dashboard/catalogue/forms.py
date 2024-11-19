from django import forms
from django.core import exceptions
from treebeard.forms import movenodeform_factory

from django.db.models.query import QuerySet
from oscar.apps.offer import queryset
from oscar.core.loading import get_class, get_classes, get_model
from oscar.core.utils import slugify
from oscar.forms.widgets import DateTimePickerInput, ImageInput, ThumbnailInput

Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
Attribute = get_model("catalogue", "Attribute")
AttributeSelect = get_class("dashboard.catalogue.widgets", "AttributeSelect")
ProductAttribute = get_model("catalogue", "ProductAttribute")
Category = get_model("catalogue", "Category")
StockRecord = get_model("partner", "StockRecord")
ProductCategory = get_model("catalogue", "ProductCategory")
ProductImage = get_model("catalogue", "ProductImage")
ProductRecommendation = get_model("catalogue", "ProductRecommendation")
ProductAdditional = get_model("catalogue", "ProductAdditional")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
AttributeOption = get_model("catalogue", "AttributeOption")
Option = get_model("catalogue", "Option")
Additional = get_model("catalogue", "Additional")
ProductSelect = get_class("dashboard.catalogue.widgets", "ProductSelect")
AdditionalSelect = get_class("dashboard.catalogue.widgets", "AdditionalSelect")
(RelatedFieldWidgetWrapper, RelatedMultipleFieldWidgetWrapper) = get_classes(
    "dashboard.widgets",
    ("RelatedFieldWidgetWrapper", "RelatedMultipleFieldWidgetWrapper"),
)


BaseCategoryForm = movenodeform_factory(
    Category,
    fields=[
        "name",
        "slug",
        "description",
        "order",
        "image",
        "is_public",
        "is_promo",
        "meta_title",
        "meta_description",
    ],
    exclude=["ancestors_are_public"],
    widgets={
        "meta_description": forms.Textarea(attrs={"class": "no-widget-init"}),
        "image": ThumbnailInput(),
        },
)


class SEOFormMixin:
    seo_fields = ["meta_title", "meta_description", "slug"]

    def primary_form_fields(self):
        return [
            field
            for field in self
            if not field.is_hidden and not self.is_seo_field(field)
        ]


    def seo_form_fields(self):
        return [field for field in self if self.is_seo_field(field)]

    def is_seo_field(self, field):
        return field.name in self.seo_fields


class CategoryForm(SEOFormMixin, BaseCategoryForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "slug" in self.fields:
            self.fields["slug"].required = False
            self.fields["slug"].help_text = (
                "Оставьте пустым, чтобы сгенерировать на основе названия категории"
            )


class ProductClassSelectForm(forms.Form):
    """
    Form which is used before creating a product to select it's product class
    """

    product_class = forms.ModelChoiceField(
        label="Создать продукт",
        empty_label="Выберите тип продукта",
        queryset=ProductClass.objects.all(),
        widget=forms.Select(attrs={
            'class': 'select-field',
        })
    )

    def __init__(self, *args, **kwargs):
        """
        If there's only one product class, pre-select it
        """
        super().__init__(*args, **kwargs)
        qs = self.fields["product_class"].queryset
        if not kwargs.get("initial") and len(qs) == 1:
            self.fields["product_class"].initial = qs[0]


class ProductSearchForm(forms.Form):
    upc = forms.CharField(max_length=64, required=False, label="Код UPC")
    title = forms.CharField(max_length=255, required=False, label="Имя продукта")
    categories = forms.ModelMultipleChoiceField(
        label="Категория",
        queryset=Category.objects.all(),
        required=False,
    )
    product_class = forms.ModelMultipleChoiceField(
        label="Тип продукта",
        queryset=ProductClass.objects.all(),
        required=False,
    )
    is_public = forms.BooleanField(
        label="Доступен",
        required=False,
        widget=forms.widgets.CheckboxInput(
            attrs={'checked': True}
        )
    )

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["upc"] = cleaned_data["upc"].strip()
        cleaned_data["title"] = cleaned_data["title"].strip()
        return cleaned_data


class StockRecordForm(forms.ModelForm):
    def __init__(self, product_class, user, *args, **kwargs):
        # The user kwarg is not used by stock StockRecordForm. We pass it
        # anyway in case one wishes to customise the partner queryset
        self.user = user
        super().__init__(*args, **kwargs)

        # If not tracking stock, we hide the fields
        if not product_class.track_stock:
            for field_name in ["num_in_stock", "low_stock_threshold"]:
                if field_name in self.fields:
                    del self.fields[field_name]
        else:
            for field_name in ["price", "num_in_stock"]:
                if field_name in self.fields:
                    self.fields[field_name].required = True

    class Meta:
        model = StockRecord
        fields = [
            "partner",
            "cost_price",
            "old_price",
            "price",
            "price_currency",
            "tax",
            "num_in_stock",
            "low_stock_threshold",
            "is_public",
        ]


class StockRecordStockForm(forms.ModelForm):
    def __init__(self, product_class, user, *args, **kwargs):
        # The user kwarg is not used by stock StockRecordForm. We pass it
        # anyway in case one wishes to customise the partner queryset
        self.user = user
        super().__init__(*args, **kwargs)

        # If not tracking stock, we hide the fields
        if not product_class.track_stock:
            for field_name in ["num_in_stock"]:
                if field_name in self.fields:
                    del self.fields[field_name]
        else:
            for field_name in ["num_in_stock"]:
                if field_name in self.fields:
                    self.fields[field_name].required = True

    class Meta:
        model = StockRecord
        fields = [
            "num_in_stock",
            "is_public",
        ]


class StockAlertSearchForm(forms.Form):
    status = forms.CharField(label="Статус")


def _attr_text_field(attribute):
    return forms.CharField(label=attribute.name, required=attribute.required)


def _attr_textarea_field(attribute):
    return forms.CharField(
        label=attribute.name, widget=forms.Textarea(), required=attribute.required
    )


def _attr_integer_field(attribute):
    return forms.IntegerField(label=attribute.name, required=attribute.required)


def _attr_boolean_field(attribute):
    return forms.BooleanField(label=attribute.name, required=attribute.required)


def _attr_float_field(attribute):
    return forms.FloatField(label=attribute.name, required=attribute.required)


def _attr_date_field(attribute):
    return forms.DateField(
        label=attribute.name,
        required=attribute.required,
        widget=forms.widgets.DateInput,
    )


def _attr_datetime_field(attribute):
    return forms.DateTimeField(
        label=attribute.name, required=attribute.required, widget=DateTimePickerInput()
    )


def _attr_option_field(attribute):
    return forms.ModelChoiceField(
        label=attribute.name,
        required=attribute.required,
        queryset=attribute.option_group.options.all(),
    )

def _attr_variant_field(attribute, value):
    return forms.ModelChoiceField(
        label=attribute.name,
        required=attribute.required,
        queryset=value,
        empty_label=None,
    )


def _attr_multi_option_field(attribute):
    return forms.ModelMultipleChoiceField(
        label=attribute.name,
        required=attribute.required,
        queryset=attribute.option_group.options.all(),   
    )


# pylint: disable=unused-argument
def _attr_entity_field(attribute):
    # Product entities don't have out-of-the-box supported in the ProductForm.
    # There is no ModelChoiceField for generic foreign keys, and there's no
    # good default behaviour anyway; offering a choice of *all* model instances
    # is hardly useful.
    return None


def _attr_numeric_field(attribute):
    return forms.FloatField(label=attribute.name, required=attribute.required)


def _attr_file_field(attribute):
    return forms.FileField(label=attribute.name, required=attribute.required)


def _attr_image_field(attribute):
    return forms.ImageField(label=attribute.name, required=attribute.required)


class ProductClassForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pylint: disable=no-member
        remote_field = self._meta.model._meta.get_field("options").remote_field
        self.fields["options"].widget = RelatedMultipleFieldWidgetWrapper(
            self.fields["options"].widget, remote_field
        )

    class Meta:
        model = ProductClass
        fields = ["name", "requires_shipping", "track_stock", "options"]


class ProductForm(SEOFormMixin, forms.ModelForm):
    FIELD_FACTORIES = {
        "text": _attr_text_field,
        "richtext": _attr_textarea_field,
        "integer": _attr_integer_field,
        "boolean": _attr_boolean_field,
        "float": _attr_float_field,
        "date": _attr_date_field,
        "datetime": _attr_datetime_field,
        "option": _attr_option_field,
        "multi_option": _attr_multi_option_field,
        "entity": _attr_entity_field,
        "numeric": _attr_numeric_field,
        "file": _attr_file_field,
        "image": _attr_image_field,
    }
    evotor_update = forms.BooleanField(
        label="Эвотор", 
        required=False, 
        initial=True,
        help_text="Синхронизировать с Эвотор", 
    )

    class Meta:
        model = Product
        fields = [
            "title",
            "upc",
            "short_description",
            "description",
            "order",
            "cooking_time",
            "is_public",
            "is_discountable",
            "structure",
            "slug",
            "meta_title",
            "meta_description",
            "evotor_update",
        ]
        widgets = {
            "structure": forms.HiddenInput(),
            "meta_description": forms.Textarea(attrs={"class": "no-widget-init"}),
        }

    def __init__(self, product_class, *args, data=None, parent=None, **kwargs):
        self.set_initial(product_class, parent, kwargs)
        super().__init__(data, *args, **kwargs)
        if parent:
            self.instance.parent = parent
            # We need to set the correct product structures explicitly to pass
            # attribute validation and child product validation. Note that
            # those changes are not persisted.
            self.instance.structure = Product.CHILD
            self.instance.parent.structure = Product.PARENT

            self.delete_non_child_fields()
            self.add_variant_fields()
        else:
            # Only set product class for non-child products
            self.instance.product_class = product_class
            self.add_attribute_fields(product_class, self.instance.is_parent)

        if "slug" in self.fields:
            self.fields["slug"].required = False
            self.fields["slug"].help_text = (
                "Оставьте поле пустым, чтобы сгенерировать из названия продукта"
            )
        if "title" in self.fields:
            self.fields["title"].widget = forms.TextInput(attrs={"autocomplete": "off"})

    def set_initial(self, product_class, parent, kwargs):
        """
        Set initial data for the form. Sets the correct product structure
        and fetches initial values for the dynamically constructed attribute
        fields.
        """
        if "initial" not in kwargs:
            kwargs["initial"] = {}
        self.set_initial_attribute_values(product_class, kwargs)
        if parent:
            kwargs["initial"]["structure"] = Product.CHILD

    def set_initial_attribute_values(self, product_class, kwargs):
        """
        Update the kwargs['initial'] value to have the initial values based on
        the product instance's attributes
        """
        instance = kwargs.get("instance")
        if instance is None:
            return
        for attribute in (product_class.class_attributes.all() | instance.attributes.all()):
            try:
                attr = instance.attribute_values.get(attribute=attribute)
                value = attr.value
                is_variant = attr.is_variant
            except exceptions.ObjectDoesNotExist:
                pass
            else:
                if instance.is_child:
                    value = value.first()

                kwargs["initial"]["attr_%s" % attribute.code] = value
                kwargs["initial"]["attr_is_variant_%s" % attribute.code] = is_variant

    def add_variant_fields(self):
        """
        For each attribute specified by the product class, this method
        dynamically adds form fields to the product form.
        """
        attribute_values = self.instance.parent.get_variant_attributes()

        for attribute_value in attribute_values:
            field = _attr_variant_field(attribute_value.attribute, attribute_value.value)
            if field:
                field.required = True
                self.fields["attr_%s" % attribute_value.attribute.code] = field

    def add_attribute_fields(self, product_class, is_parent=False):
        """
        For each attribute specified by the product class, this method
        dynamically adds form fields to the product form.
        """
        if self.instance.id:
            attributes = product_class.class_attributes.all() | self.instance.attributes.all()
        else:
            attributes = product_class.class_attributes.all()

        for attribute in attributes:
            field = self.get_attribute_field(attribute)
            if field:
                if is_parent:
                    field.required = False

                self.fields["attr_%s" % attribute.code] = field
                if attribute.type == "multi_option":
                    self.fields["attr_is_variant_%s" % attribute.code] = forms.BooleanField(
                        required=False,
                        label="Используется для вариаций?",
                        help_text="Данный атрибут можно использовать при создании вариативного продукта.",

                    )

    def get_attribute_field(self, attribute):
        """
        Gets the correct form field for a given attribute type.
        """
        return self.FIELD_FACTORIES[attribute.type](attribute)

    def delete_non_child_fields(self):
        """
        Deletes any fields not needed for child products. Override this if
        you want to e.g. keep the description field.
        """
        for field_name in ["description", "short_description", "is_discountable", "meta_title", "meta_description"]:
            if field_name in self.fields:
                del self.fields[field_name]     

    def clean_evotor_update(self):
        evotor_update = self.cleaned_data.get('evotor_update')
        if evotor_update:
            fff = 1           

    def _post_clean(self):
        """
        Set attributes before ModelForm calls the product's clean method
        (which it does in _post_clean), which in turn validates attributes.
        """
        for attribute in self.instance.attr.get_all_attributes():
            field_name = "attr_%s" % attribute.code
            is_variant_name = "attr_is_variant_%s" % attribute.code
            # An empty text field won't show up in cleaned_data.
            if field_name in self.cleaned_data:
                value = self.cleaned_data[field_name]
                if attribute.type == 'multi_option' and not isinstance(value, QuerySet):
                    value = [value] 

                setattr(self.instance.attr, attribute.code, value)
            
            if self.instance.id:
                if is_variant_name in self.cleaned_data:
                    value = self.cleaned_data[is_variant_name]
                    attribute_obj = self.instance.attribute_values.filter(attribute=attribute).first()
                    if attribute_obj:
                        attribute_obj.is_variant = value
                        attribute_obj.save()

        super()._post_clean()


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ("category",)


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["product", "original", "caption", "display_order"]
        # use ImageInput widget to create HTML displaying the
        # actual uploaded image and providing the upload dialog
        # when clicking on the actual image.
        widgets = {
            "original": ImageInput(),
            "display_order": forms.HiddenInput(),
        }

    def __init__(self, *args, data=None, **kwargs):
        self.prefix = kwargs.get("prefix", None)
        instance = kwargs.get("instance", None)
        if not instance:
            initial = {"display_order": self.get_display_order()}
            initial.update(kwargs.get("initial", {}))
            kwargs["initial"] = initial
        super().__init__(data, *args, **kwargs)

    def get_display_order(self):
        return int(self.prefix.split("-").pop())


class ProductRecommendationForm(forms.ModelForm):
    class Meta:
        model = ProductRecommendation
        fields = ["primary", "recommendation", "ranking"]
        widgets = {
            "recommendation": ProductSelect,
        }


class AdditionalForm(forms.ModelForm):
    class Meta:
        model = Additional
        fields = ["name", "upc", "order", "description", "price_currency", "price", "old_price", "weight", "max_amount", "image"]
        widgets = {
            "image": ThumbnailInput(),
        }


class ProductAdditionalForm(forms.ModelForm):
    class Meta:
        model = ProductAdditional
        fields = ["primary_product", "additional_product", "ranking"]
        widgets = {
            "additional_product": AdditionalSelect,
        }


class ProductClassAdditionalForm(forms.ModelForm):
    class Meta:
        model = ProductAdditional
        fields = ["primary_class", "additional_product", "ranking"]
        widgets = {
            "additional_product": AdditionalSelect,
        }


class AttributeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # because we'll allow submission of the form with blank
        # codes so that we can generate them.
        self.fields["code"].required = False

        # self.fields["option_group"].help_text = "Выберите группу опций"

        # pylint: disable=no-member
        remote_field = self._meta.model._meta.get_field("option_group").remote_field
        self.fields["option_group"].widget = RelatedFieldWidgetWrapper(
            self.fields["option_group"].widget, remote_field
        ) 

    def clean_code(self):
        code = self.cleaned_data.get("code")
        title = self.cleaned_data.get("name")

        if not code and title:
            code = slugify(title)

        return code

    def clean(self):
        attr_type = self.cleaned_data.get("type")
        option_group = self.cleaned_data.get("option_group")
        if (
            attr_type in [Attribute.OPTION, Attribute.MULTI_OPTION]
            and not option_group
        ):
            self.add_error("option_group", "Требуется группа опций.")

    class Meta:
        model = Attribute
        fields = ["name", "code", "type", "option_group", "required"]


class ProductAttributesForm(forms.ModelForm):
    class Meta:
        model = ProductAttribute
        fields = ["product", "attribute"]
        widgets = {
            "attribute": AttributeSelect,
        }


class ProductClassAttributesForm(forms.ModelForm):
    class Meta:
        model = ProductAttribute
        fields = ["product_class", "attribute"]
        widgets = {
            "attribute": AttributeSelect,
        }


class AttributeOptionGroupForm(forms.ModelForm):
    class Meta:
        model = AttributeOptionGroup
        fields = ["name"]


class AttributeOptionForm(forms.ModelForm):
    class Meta:
        model = AttributeOption
        fields = ["option"]


class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ["name", "type", "required", "order", "help_text", "option_group"]
