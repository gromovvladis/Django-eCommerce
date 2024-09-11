# pylint: disable=unused-argument
from django import forms
from django.conf import settings
from django.core.validators import EMPTY_VALUES
from django.forms.utils import ErrorDict
from django.db.models import Sum
from oscar.core.loading import get_model

Line = get_model("basket", "line")
Basket = get_model("basket", "basket")
Option = get_model("catalogue", "option")
Product = get_model("catalogue", "product")

def _option_text_field(form, product, option):
    return forms.CharField(
        label=option.name, required=option.required, help_text=option.help_text,
    )


def _option_integer_field(form, product, option):
    return forms.IntegerField(
        label=option.name, required=option.required, help_text=option.help_text,
    )


def _option_boolean_field(form, product, option):
    return forms.BooleanField(
        label=option.name, required=option.required, help_text=option.help_text,
    )


def _option_float_field(form, product, option):
    return forms.FloatField(
        label=option.name, required=option.required, help_text=option.help_text,
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
        widget=forms.widgets.NumberInput(attrs={
            'additional': True,
            'image': additional.primary_image,
            'price': additional.price, 
            'old_price': additional.old_price,
            'weight': additional.weight,
            'min': 0,
            'max': additional.max_amount,
            'readonly': True,
        }),
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
            max_allowed_quantity = None
            num_available = getattr(
                self.instance.purchase_info.availability, "num_available", None
            ) 
            if num_available is not None:
                num_available = num_available + self.instance.quantity

            basket_max_allowed_quantity = self.instance.basket.max_allowed_quantity()[0] + self.instance.quantity
            if all([num_available, basket_max_allowed_quantity]):
                max_allowed_quantity = min(num_available, basket_max_allowed_quantity)
            else:
                max_allowed_quantity = basket_max_allowed_quantity or num_available
                
            if max_allowed_quantity:
                self.fields["quantity"].widget.attrs["max"] = max_allowed_quantity

    # pylint: disable=W0201
    def full_clean(self):
        if not self.instance.id:
            self.cleaned_data = {}
            self._errors = ErrorDict()
            return
        return super().full_clean()

    def has_changed(self):
        if not self.instance.id:
            return False
        return super().has_changed()

    def clean_quantity(self):
        qty = self.cleaned_data["quantity"] or 0
        if qty > 0:
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
        policy = self.instance.purchase_info.availability
        is_available, reason = policy.is_purchase_permitted(quantity=qty)
        if not is_available:
            raise forms.ValidationError(reason)

    class Meta:
        model = Line
        fields = ["quantity"]


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

    quantity = forms.IntegerField(initial=1, min_value=1, label="Количество", required=False)

    def __init__(self, basket, product, *args, **kwargs):
        # Note, the product passed in here isn't necessarily the product being
        # added to the basket. For child products, it is the *parent* product
        # that gets passed to the form. An optional product_id param is passed
        # to indicate the ID of the child product being added to the basket.
        self.basket = basket
        self.parent_product = product

        super().__init__(*args, **kwargs)

        # Dynamically build fields
        if product.is_parent:
            self._create_parent_product_fields(product)

        self._create_product_fields(product)

    def _create_parent_product_fields(self, product):
        """
        Adds the fields for a "group"-type product (eg, a parent product with a
        list of children.

        Currently requires that a stock record exists for the children
        """
        choices = []
        disabled_values = []
        for child in product.children.order_by('order').public():
            # Build a description of the child, including any pertinent
            # attributes
            stc = child.stockrecords.all()[0]
            summary = {'name':child.get_variant(), 'price':stc.price, 'old_price':stc.old_price}
            # Check if it is available to buy
            info = self.basket.strategy.fetch_for_product(child)
            if not info.availability.is_available_to_buy:
                disabled_values.append(child.id)

            if child.id not in disabled_values:
                choices.append((child.id, summary))

        self.fields["child_id"] = forms.ChoiceField(
            choices=tuple(choices),
            label="Вариант",
            widget=forms.widgets.RadioSelect(),
        )


    def _create_product_fields(self, product):
        """
        Add the product option fields.
        """
        for option in product.options:
            self._add_option_field(product, option)
        
        for additional in product.additionals:
            self._add_additional_field(product, additional)
            

    def _add_option_field(self, product, option):
        """
        Creates the appropriate form field for the product option.

        This is designed to be overridden so that specific widgets can be used
        for certain types of options.
        """
        option_field = self.OPTION_FIELD_FACTORIES.get(option.type, _option_text_field)(
            self, product, option
        )
        self.fields[option.code] = option_field

    def _add_additional_field(self, product, additional):
        """
        Creates the appropriate form field for the product option.

        This is designed to be overridden so that specific widgets can be used
        for certain types of options.
        """
        additional_field = _good_field(self, product, additional)
        self.fields[additional.code] = additional_field

    # Cleaning

    def clean_child_id(self):
        try:
            child = self.parent_product.children.get(id=self.cleaned_data["child_id"])
        except Product.DoesNotExist:
            raise forms.ValidationError("Пожалуйста, выберите корректный продукт")

        # To avoid duplicate SQL queries, we cache a copy of the loaded child
        # product as we're going to need it later.
        self.child_product = child  # pylint: disable=W0201

        return self.cleaned_data["child_id"]

    def clean_quantity(self):
        # Check that the proposed new line quantity is sensible
        qty = self.cleaned_data["quantity"]
        if not qty:
            qty = 1
            
        basket_threshold = settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD
        if basket_threshold:
            total_basket_quantity = self.basket.num_items
            max_allowed = basket_threshold - total_basket_quantity
            if qty > max_allowed:
                raise forms.ValidationError(
                    (
                        "Из-за технических ограничений мы не можем отправить более "
                        "%(threshold)d товаров в одном заказе. В настоящее время в вашей корзине %(basket)d товаров."
                    )
                    % {"threshold": basket_threshold, "basket": total_basket_quantity}
                )
        return qty

    @property
    def product(self):
        """
        The actual product being added to the basket
        """
        # Note, the child product attribute is saved in the clean_child_id
        # method
        return getattr(self, "child_product", self.parent_product)

    def clean(self):
        info = self.basket.strategy.fetch_for_product(self.product)

        # Check that a price was found by the strategy
        if not info.price.exists:
            raise forms.ValidationError(
                (
                "Этот товар нельзя добавить в корзину, поскольку для него не удалось определить цену."
                )
            )

        # Check currencies are sensible
        if self.basket.currency and info.price.currency != self.basket.currency:
            raise forms.ValidationError(
                (
                    "Этот товар нельзя добавить в корзину, поскольку его валюта не совпадает с валютой других товаров в вашей корзине."
                )
            )

        # Check user has permission to add the desired quantity to their
        # basket.
        current_qty = self.basket.product_quantity(self.product)
        desired_qty = current_qty + self.cleaned_data.get("quantity", 1)
        is_permitted, reason = info.availability.is_purchase_permitted(desired_qty)
        if not is_permitted:
            raise forms.ValidationError(reason)

        return self.cleaned_data

    # Helpers

    def cleaned_options(self):
        """
        Return submitted options in a clean format
        """
        options = []
        for option in self.parent_product.options:
            if option.code in self.cleaned_data:
                value = self.cleaned_data[option.code]
                if option.required or value not in EMPTY_VALUES:
                    options.append({"option": option, "value": value})
        return options
    
    
    def cleaned_additionals(self):
        """
        Return submitted options in a clean format
        """
        additionals = []
        for additional in self.product.additionals:
            if additional.code in self.cleaned_data:
                value = self.cleaned_data[additional.code]
                if value not in EMPTY_VALUES and value > 0:
                    additionals.append({"additional": additional, "value": value})
        return additionals


class SimpleAddToBasketMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "quantity" in self.fields:
            self.fields["quantity"].initial = 1
            # self.fields["quantity"].widget = forms.HiddenInput()


class SimpleAddToBasketForm(SimpleAddToBasketMixin, AddToBasketForm):
    pass
    """
    Simplified version of the add to basket form where the quantity is
    defaulted to 1 and rendered in a hidden widget

    If you changed `AddToBasketForm`, you'll need to override this class
    as well by doing:

    class SimpleAddToBasketForm(SimpleAddToBasketMixin, AddToBasketForm):
        pass
    """


class SavedLineForm(forms.ModelForm):
    move_to_basket = forms.BooleanField(
        initial=False, required=False, label="Добавить в корзину"
    )

    class Meta:
        model = Line
        fields = ("id", "move_to_basket")

    def __init__(self, strategy, basket, *args, **kwargs):
        self.strategy = strategy
        self.basket = basket
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data["move_to_basket"]:
            # skip further validation (see issue #666)
            return cleaned_data

        # Get total quantity of all lines with this product (there's normally
        # only one but there can be more if you allow product options).
        lines = self.basket.lines.filter(product=self.instance.product)
        current_qty = lines.aggregate(Sum("quantity"))["quantity__sum"] or 0
        desired_qty = current_qty + self.instance.quantity

        result = self.strategy.fetch_for_product(self.instance.product)
        is_available, reason = result.availability.is_purchase_permitted(
            quantity=desired_qty
        )
        if not is_available:
            raise forms.ValidationError(reason)
        return cleaned_data
