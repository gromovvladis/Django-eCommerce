import datetime
from django import forms
from django.conf import settings
from django.http import QueryDict

from oscar.apps.payment.models import Source, Transaction
from oscar.core.loading import get_class, get_model
from oscar.forms.mixins import PhoneNumberMixin
from oscar.forms.widgets import DatePickerInput

Order = get_model("order", "Order")
OrderNote = get_model("order", "OrderNote")
ShippingAddress = get_model("order", "ShippingAddress")
SourceType = get_model("payment", "SourceType")
AbstractAddressForm = get_class("address.forms", "AbstractAddressForm")


class OrderStatsForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        label=("Дата начала", "От"),
        widget=DatePickerInput,
    )
    date_to = forms.DateField(
        required=False, label=("Дата окончания", "До"), widget=DatePickerInput
    )

    _filters = _description = None

    def _determine_filter_metadata(self):
        self._filters = {}
        self._description = "Все заказы"
        if self.errors:
            return

        date_from = self.cleaned_data["date_from"]
        date_to = self.cleaned_data["date_to"]
        if date_from and date_to:
            # We want to include end date so we adjust the date we use with the
            # 'range' function.
            self._filters = {
                "date_placed__range": [date_from, date_to + datetime.timedelta(days=1)]
            }
            self._description = (
                "Заказы размещены между %(date_from)s и %(date_to)s"
            ) % {"date_from": date_from, "date_to": date_to}
        elif date_from and not date_to:
            self._filters = {"date_placed__gte": date_from}
            self._description = ("Заказы размещены с %s") % (date_from,)
        elif not date_from and date_to:
            self._filters = {"date_placed__lte": date_to}
            self._description = ("Заказы размещены до %s") % (date_to,)
        else:
            self._filters = {}
            self._description = "Все заказы"

    def get_filters(self):
        if self._filters is None:
            self._determine_filter_metadata()
        return self._filters

    def get_filter_description(self):
        if self._description is None:
            self._determine_filter_metadata()
        return self._description


class OrderSearchForm(forms.Form):
    order_number = forms.CharField(required=False, label="Номер заказа")
    name = forms.CharField(required=False, label="Имя Клиента")
    product_title = forms.CharField(required=False, label="Наименование товара")
    upc = forms.CharField(required=False, label="Товарный код продукта UPC")
    partner_sku = forms.CharField(required=False, label="Артикул в точке продажи")

    status_choices = (("", "---------"),) + tuple(
        [(v, v) for v in Order.all_statuses()]
    )
    status = forms.ChoiceField(
        choices=status_choices, label="Статус", required=False
    )

    date_from = forms.DateField(
        required=False, label="Дата с", widget=DatePickerInput
    )
    date_to = forms.DateField(
        required=False, label="Дата до", widget=DatePickerInput
    )

    voucher = forms.CharField(required=False, label="Промокод")

    payment_method = forms.ChoiceField(
        label="Способ оплаты", required=False, choices=()
    )

    format_choices = (
        ("html", "HTML"),
        ("csv", "CSV"),
    )
    response_format = forms.ChoiceField(
        widget=forms.RadioSelect,
        required=False,
        choices=format_choices,
        initial="html",
        label="Получите результаты как",
    )

    def __init__(self, *args, **kwargs):
        # Ensure that 'response_format' is always set
        if "data" in kwargs:
            data = kwargs["data"]
            del kwargs["data"]
        elif len(args) > 0:
            data = args[0]
            args = args[1:]
        else:
            data = None

        if data:
            if data.get("response_format", None) not in self.format_choices:
                # Handle POST/GET dictionaries, which are immutable.
                if isinstance(data, QueryDict):
                    data = data.dict()
                data["response_format"] = "html"

        super().__init__(data, *args, **kwargs)
        self.fields["payment_method"].choices = self.payment_method_choices()

    def payment_method_choices(self):
        return (("", "---------"),) + tuple(
            [(src.code, src.name) for src in SourceType.objects.all()]
        )


class OrderNoteForm(forms.ModelForm):
    class Meta:
        model = OrderNote
        fields = ["message"]

    def __init__(self, order, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.order = order
        self.instance.user = user


class ShippingAddressForm(PhoneNumberMixin, AbstractAddressForm):
    class Meta:
        model = ShippingAddress
        fields = [
            "line1",
            "line2",
            "line3",
            "line4",
            "notes",
        ]


class OrderStatusForm(forms.Form):
    new_status = forms.ChoiceField(label="Статус нового заказа", choices=())

    def __init__(self, order, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set the choices
        choices = [(x, x) for x in order.available_statuses()]
        self.fields["new_status"].choices = choices

    @property
    def has_choices(self):
        return len(self.fields["new_status"].choices) > 0


class NewSourceForm(forms.ModelForm):


    def __init__(self, order, *args, **kwargs):
        
        super().__init__(*args, **kwargs)

        self.order = order
        source_type_list = []
        
        payment_chouces = settings.WEBSHOP_PAYMENT_CHOICES
        for chs in payment_chouces:
            source_type_list.append(chs[1])

        queryset = SourceType.objects.filter(name__in=source_type_list)

        self.fields["source_type"].queryset = queryset
        self.fields["source_type"].initial = queryset.first()
        self.fields["amount_allocated"].widget.attrs.update({'max': order.total})
        self.fields["amount_allocated"].initial = order.total


    source_type = forms.ModelChoiceField(
        queryset=Source.objects.none(),
        label='Способ оплаты',
        required=True,
        help_text='Выберите для какого способа оплаты создате транзакцию',
    )

    amount_allocated = forms.DecimalField(
        label="Сумма", min_value=0, required=False, help_text='Сумма к оплате'
    )
    payment_id = forms.CharField(max_length=128, label="Код платежа", required=False, help_text='Код оплаты (для интернет транзакций)')
    refund_id = forms.CharField(max_length=128, label="Код возврата", required=False, help_text='Код возврата (для интернет транзакций)')


    class Meta:
        model = Source
        fields = [
            "source_type",
            "amount_allocated", 
            "payment_id",
            "refund_id",
        ]


class NewTransactionForm(forms.ModelForm):

    def __init__(self, order, *args, **kwargs):
        
        super().__init__(*args, **kwargs)

        self.order = order

        txn_type_choices = (('Refund', 'Оплата'), ('Refund', 'Возврат'))
        status_choices = (('succeeded', 'Успешно'), ('canceled', 'Отклонен'), ('pending', 'Обработка'))
        queryset = Source.objects.filter(order_id=order.id)

        self.fields["source"].queryset = queryset
        self.fields["source"].initial = queryset.first()
        self.fields["txn_type"].choices = txn_type_choices
        self.fields["status"].choices = status_choices
        self.fields["amount"].widget.attrs.update({'max': order.total})
        self.fields["amount"].initial = order.total


    source = forms.ModelChoiceField(
        queryset=Source.objects.none(),
        label='Способ оплаты',
        required=True,
        help_text='Выберите для какого способа оплаты создате транзакцию',
    )

    status = forms.ChoiceField(
        label='Статус транзакции',
        required=True,
        help_text='Выберите статус транзакции',
    )

    txn_type = forms.ChoiceField(
        label='Тип операции',
        required=True,
        help_text='Оплата или возврат',
    )

    amount = forms.DecimalField(
        label="Сумма", min_value=0, required=False, help_text='Сумма транзакции'
    )

    code = forms.CharField(max_length=128, label="Код", required=False, help_text='Код для интернет транзакций')
    paid = forms.BooleanField(initial=True, label="Оплачено", required=False, help_text='Заказ оплачен?')
    refundable = forms.BooleanField(initial=True, label="Возврат осуществлен", required=False, help_text='Оплату возможно вернуть?')

    class Meta:
        model = Transaction
        fields = [
            "source",
            "txn_type", 
            "amount", 
            "code", 
            "status",
            "paid", 
            "refundable", 
        ]