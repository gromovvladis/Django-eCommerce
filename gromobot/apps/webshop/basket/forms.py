# pylint: disable=unused-argument
import json

from core.loading import get_class, get_model
from django import forms
from django.conf import settings
from django.core.validators import EMPTY_VALUES
from django.forms.utils import ErrorDict

Unavailable = get_class("webshop.store.availability", "Unavailable")

Line = get_model("basket", "Line")
Basket = get_model("basket", "Basket")
Option = get_model("catalogue", "Option")
Product = get_model("catalogue", "Product")


def _option_text_field(form, product, option):
    return forms.CharField(
        label=option.name,
        required=option.required,
        help_text=option.help_text,
    )


def _option_integer_field(form, product, option):
    return forms.IntegerField(
        label=option.name,
        required=option.required,
        help_text=option.help_text,
    )


def _option_boolean_field(form, product, option):
    return forms.BooleanField(
        label=option.name,
        required=option.required,
        help_text=option.help_text,
    )


def _option_float_field(form, product, option):
    return forms.FloatField(
        label=option.name,
        required=option.required,
        help_text=option.help_text,
    )


def _option_date_field(form, product, option):
    return forms.DateField(
        label=option.name,
        required=option.required,
        widget=forms.widgets.SelectDateWidget,
        help_text=option.help_text,
    )


def _option_select_field(form, product, option):
    return forms.ChoiceField(
        label=option.name,
        required=option.required,
        choices=option.get_choices(),
        help_text=option.help_text,
    )


def _option_radio_field(form, product, option):
    return forms.ChoiceField(
        label=option.name,
        required=option.required,
        choices=option.get_choices(),
        widget=forms.RadioSelect,
        help_text=option.help_text,
    )


def _option_multi_select_field(form, product, option):
    return forms.MultipleChoiceField(
        label=option.name,
        required=option.required,
        choices=option.get_choices(),
        help_text=option.help_text,
    )


def _option_checkbox_field(form, product, option):
    return forms.MultipleChoiceField(
        label=option.name,
        required=option.required,
        choices=option.get_choices(),
        widget=forms.CheckboxSelectMultiple,
        help_text=option.help_text,
    )


def _good_field(form, product, additional):
    return forms.IntegerField(
        label=additional.name,
        initial=0,
        required=False,
        widget=forms.widgets.NumberInput(
            attrs={
                "additional": True,
                "image": additional.primary_image,
                "price": additional.price,
                "old_price": additional.old_price,
                "weight": additional.weight,
                "min": 0,
                "max": additional.max_amount,
                "readonly": True,
            }
        ),
    )


class BasketLineForm(forms.ModelForm):
    is_ajax_updated = True

    quantity = forms.IntegerField(
        label="Количество", min_value=0, required=False, initial=1
    )

    def __init__(self, strategy, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.strategy = strategy

        # Evaluate max allowed quantity check only if line still exists, in
        # order to avoid check run against missing instance -
        # https://github.com/django-oscar/django-oscar/issues/2873.
        if self.instance.id:
            num_available = getattr(
                self.instance.purchase_info.availability, "num_available", None
            )
            num_available = (
                num_available if num_available is not None else self.instance.quantity
            )
            basket_max_allowed_quantity = (
                self.instance.basket.max_allowed_quantity()[0] + self.instance.quantity
            )
            max_allowed_quantity = (
                min(num_available, basket_max_allowed_quantity)
                if all([num_available, basket_max_allowed_quantity])
                else basket_max_allowed_quantity or num_available
            )
            if max_allowed_quantity:
                self.fields["quantity"].widget.attrs["max"] = max_allowed_quantity

    # pylint: disable=W0201
    def full_clean(self):
        if not self.instance.id:
            self.cleaned_data, self._errors = {}, ErrorDict()
            return
        return super().full_clean()

    def has_changed(self):
        return self.instance.id and super().has_changed()

    def clean_quantity(self):
        qty = self.cleaned_data.get("quantity", 0)
        if (
            not isinstance(self.instance.purchase_info.availability, Unavailable)
            and qty > 0
        ):
            self.check_max_allowed_quantity(qty)
            self.check_permission(qty)
        return qty

    def check_max_allowed_quantity(self, qty):
        # Since `Basket.is_quantity_allowed` checks quantity of added product
        # against total number of the products in the basket, instead of sending
        # updated quantity of the product, we send difference between current
        # number and updated. Thus, product already in the basket and we don't
        # add second time, just updating number of items.
        qty_delta = qty - self.instance.quantity
        is_allowed, reason = self.instance.basket.is_quantity_allowed(
            qty_delta, line=self.instance
        )
        if not is_allowed:
            raise forms.ValidationError(reason)

    def check_permission(self, qty):
        is_available, reason = (
            self.instance.purchase_info.availability.is_purchase_permitted(quantity=qty)
        )
        if not is_available:
            raise forms.ValidationError(reason)

    class Meta:
        model = Line
        fields = ("quantity",)


class AddToBasketForm(forms.Form):
    OPTION_FIELD_FACTORIES = {
        Option.TEXT: _option_text_field,
        Option.INTEGER: _option_integer_field,
        Option.BOOLEAN: _option_boolean_field,
        Option.FLOAT: _option_float_field,
        Option.DATE: _option_date_field,
        Option.SELECT: _option_select_field,
        Option.RADIO: _option_radio_field,
        Option.MULTI_SELECT: _option_multi_select_field,
        Option.CHECKBOX: _option_checkbox_field,
    }

    def __init__(self, basket, product, store_id, *args, **kwargs):
        # Note, the product passed in here isn't necessarily the product being
        # added to the basket. For child products, it is the *parent* product
        # that gets passed to the form. An optional product_id param is passed
        # to indicate the ID of the child product being added to the basket.
        self.store_id = store_id
        self.basket = basket
        self.parent_product = product
        self.has_additions = False
        super().__init__(*args, **kwargs)

        # Dynamically build fields
        if product.is_parent:
            self._create_parent_product_fields(product)
        self._create_product_fields(product)

    def _create_parent_product_fields(self, product):
        childs_data = [
            {
                child.id: {
                    "attr": {
                        attr.attribute.code: (
                            attr.value.first().id if attr.value.exists() else None
                        )
                        for attr in child.attribute_values.all()
                    },
                    "price": getattr(child.stockrecord, "price", None),
                    "old_price": getattr(child.stockrecord, "old_price", None),
                }
            }
            for child in product.children.public()
        ]

        self.fields["child_id"] = forms.CharField(
            initial=list(childs_data[0].keys())[0],
            widget=forms.HiddenInput(
                attrs={"data-childs": json.dumps(childs_data), "variant": True}
            ),
        )

        default_attr = childs_data[0][next(iter(childs_data[0]))]["attr"]
        attributes = {
            attr.attribute.code: (
                attr.attribute.name,
                [(val.id, val.option) for val in attr.value],
            )
            for attr in product.attribute_values.filter(is_variant=True).select_related(
                "attribute"
            )
        }

        for attribute_code, (label, choices) in attributes.items():
            initial_value = default_attr.get(attribute_code, None)
            self.fields[attribute_code] = forms.ChoiceField(
                choices=tuple(choices),
                label=label,
                initial=initial_value,
                required=False,
                widget=forms.widgets.RadioSelect(
                    attrs={
                        "variant": True,
                        "left": f"{100 / len(choices) * (next((i + 1 for i, (val, _) in enumerate(choices) if val == initial_value), 0) - 1):.2f}%",
                    }
                ),
            )

    def _create_product_fields(self, product):
        """
        Add the product option fields.
        """
        for option in product.options:
            self._add_option_field(product, option)

        for additional in product.additionals:
            if self.store_id in additional.stores.values_list("id", flat=True):
                self._add_additional_field(product, additional)
                self.has_additions = True

    def _add_option_field(self, product, option):
        """
        Creates the appropriate form field for the product option.

        This is designed to be overridden so that specific widgets can be used
        for certain types of options.
        """
        self.fields[option.code] = self.OPTION_FIELD_FACTORIES.get(
            option.type, _option_text_field
        )(self, product, option)

    def _add_additional_field(self, product, additional):
        """
        Creates the appropriate form field for the product option.

        This is designed to be overridden so that specific widgets can be used
        for certain types of options.
        """
        self.fields[additional.article] = _good_field(self, product, additional)

    # Cleaning

    def clean_child_id(self):
        try:
            child = self.parent_product.children.get(id=self.cleaned_data["child_id"])
        except Product.DoesNotExist:
            raise forms.ValidationError("Данный вариант временно недоступен.")
        self.child_product = child
        return self.cleaned_data["child_id"]

    def clean_quantity(self):
        qty = 1
        basket_threshold = settings.MAX_BASKET_QUANTITY_THRESHOLD
        if basket_threshold and self.basket.num_items + qty > basket_threshold:
            raise forms.ValidationError(
                f"Из-за технических ограничений мы не можем отправить более {basket_threshold} товаров в одном заказе. В вашей корзине {self.basket.num_items} товаров."
            )
        return qty

    def clean(self):
        info = self.basket.strategy.fetch_for_product(self.product)
        if not info.price.exists:
            raise forms.ValidationError("Этот товар нельзя добавить в корзину.")
        if self.basket.currency and info.price.currency != self.basket.currency:
            raise forms.ValidationError(
                "Этот товар нельзя добавить в корзину, так как валюты не совпадают."
            )
        current_qty = self.basket.product_quantity(self.product)
        is_permitted, reason = info.availability.is_purchase_permitted(current_qty + 1)
        if not is_permitted:
            raise forms.ValidationError(reason)
        return self.cleaned_data

    def cleaned_options(self):
        return [
            {"option": option, "value": self.cleaned_data[option.code]}
            for option in self.parent_product.options
            if option.code in self.cleaned_data
            and (option.required or self.cleaned_data[option.code] not in EMPTY_VALUES)
        ]

    def cleaned_additionals(self):
        return [
            {"additional": additional, "value": self.cleaned_data[additional.article]}
            for additional in self.product.additionals
            if additional.article in self.cleaned_data
            and self.cleaned_data[additional.article] not in EMPTY_VALUES
            and self.cleaned_data[additional.article] > 0
        ]

    @property
    def product(self):
        return getattr(self, "child_product", self.parent_product)


class SimpleAddToBasketForm(AddToBasketForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "quantity" in self.fields:
            self.fields["quantity"].initial = 1

    """
    Simplified version of the add to basket form where the quantity is
    defaulted to 1 and rendered in a hidden widget

    If you changed `AddToBasketForm`, you'll need to override this class
    as well by doing:

    class SimpleAddToBasketForm(SimpleAddToBasketMixin, AddToBasketForm):
        pass
    """
