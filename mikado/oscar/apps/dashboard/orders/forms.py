import re
import datetime
from django import forms
from django.conf import settings
from django.http import QueryDict

from oscar.apps.payment.models import Source, Transaction
from oscar.core.loading import get_class, get_model
from oscar.forms.mixins import PhoneNumberMixin
from oscar.forms.widgets import DatePickerInput, DateRangeInput

Partner = get_model("partner", "Partner")
Order = get_model("order", "Order")
OrderNote = get_model("order", "OrderNote")
ShippingAddress = get_model("order", "ShippingAddress")
SourceType = get_model("payment", "SourceType")


class OrderStatsForm(forms.Form):
    date_range = forms.CharField(
        required=False,
        label="Диапазон дат",
        widget=DateRangeInput,
    )
    date_from = forms.DateField(
        required=False,
        label="Дата начала",
        widget=DatePickerInput,
    )
    date_to = forms.DateField(
        required=False, label="Дата окончания", widget=DatePickerInput
    )
    order_number = forms.CharField(
        required=False, 
        label="Номер заказа",
        widget=forms.TextInput(attrs={
            'placeholder': '100000',
        }),)
    username = forms.CharField(
        required=False, 
        label="Телефон клиента", 
        widget=forms.TextInput(attrs={
            'placeholder': '+7 (900) 000-0000',
        }),
    )
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

    _filters = _description = _search_filters = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_method"].choices = self.payment_method_choices()

    def _determine_filter_metadata(self):
        self._filters = {}
        self._search_filters = []
        self._description = "Все заказы"
        
        if self.errors:
            return

        data = self.cleaned_data

        date_from = data.get("date_from")
        date_to = data.get("date_to")
        date_range = data.get("date_range")

        product_title = data.get("title")
        username = data.get("username")
        upc = data.get("upc")
        partner_sku = data.get("partner_sku")
        voucher = data.get("voucher")
        payment_method = data.get("payment_method")
        status = data.get("status")

        if date_from and date_to:
            # self._filters["date_placed__range"] = [date_from, date_to + datetime.timedelta(days=1)]
            self._filters["date_placed__range"] = [date_from, date_to]
            self._search_filters.append((
                ("Размещено между {start_date} и {end_date}").format(
                    start_date=date_from.strftime('%d.%m.%Y'), end_date=date_to.strftime('%d.%m.%Y')
                ), (("date_range", [date_from, date_to]),)
            ))
        elif date_from and not date_to:
            self._filters["date_placed__gte"] = date_from
            self._search_filters.append((
                ("Размещено после {start_date}").format(start_date=date_from.strftime('%d.%m.%Y')), (("date_from", date_from),)
            ))
        elif not date_from and date_to:
            self._filters["date_placed__lte"] = date_to
            self._search_filters.append((
                ("Размещено до {end_date}").format(end_date=date_to.strftime('%d.%m.%Y')), (("date_to", date_to),)
            ))
        elif date_range:
            date_from, date_to = self._format_date_range(date_range) 
            if date_from and date_to:
                # self._filters["date_placed__range"] = [date_from, date_to + datetime.timedelta(days=1)]
                self._filters["date_placed__range"] = [date_from, date_to]
                self._search_filters.append((
                    ("Размещено между {start_date} и {end_date}").format(
                        start_date=date_from.strftime('%d.%m.%Y'), end_date=date_to.strftime('%d.%m.%Y')
                    ), (("date_range", [date_from, date_to]),)
                ))
            
        if product_title:
            self._filters["lines__title__istartswith"] = product_title
            self._search_filters.append((
                ('Название продукта соответствует "{title}"').format(
                    title=product_title
                ), (("product_title", product_title),)
            ))

        if username:
            self._filters["user__username__istartswith"] = username
            self._search_filters.append((
                ('Номер клиента совпадает с "{name}"').format(
                    name=username
                ), (("username", username),)
            ))

        if upc:
            self._filters["lines__upc"] = upc
            self._search_filters.append((
                ('Включает предмет с UPC "{prod_upc}"').format(prod_upc=upc), (("upc", upc),)
            ))

        if partner_sku:
            self._filters["lines__partner_sku"] = partner_sku
            self._search_filters.append((
                ('Включает товар с артикулом партнера. "{sku}"').format(
                    sku=partner_sku
                ), (("partner_sku", partner_sku),)
            ))

        if voucher:
            self._filters["discounts__voucher_code"] = voucher
            self._search_filters.append((
                ('Использованный промокод "{code}"').format(
                    code=voucher
                ), (("voucher", voucher),)
            ))

        if payment_method:
            self._filters["sources__source_type__code"] = payment_method
            self._search_filters.append((
                ("Оплачено с помощью {method}").format(
                    method=payment_method.name
                ), (("payment_method", payment_method),)
            ))

        if status:
            self._filters["status"] = status
            self._search_filters.append((
                ("Статус заказа {sts}").format(sts=status), (("status", status),)
            ))

        if self._filters:
            self._description = "Результаты поиска"

    def get_filters(self):
        if self._filters is None:
            self._determine_filter_metadata()
        return self._filters

    def get_search_filters(self):
        if self._search_filters is None:
            self._determine_filter_metadata()
        return self._search_filters

    def get_filter_description(self): 
        if self._description is None:
            self._determine_filter_metadata()
        return self._description

    def format_phone_number(self, phone_number):
        # Простейший способ форматирования номера телефона
        phone_number = re.sub(r'\D', '', phone_number)  # Удаляем все нецифровые символы
        if len(phone_number) == 11 and phone_number.startswith('7'):
            phone_number = '+7 ({}) {}-{}'.format(
                phone_number[1:4],
                phone_number[4:7],
                phone_number[7:]
            )
        return phone_number
    
    def _format_date_range(self, range):
        ranges = range.split('-')
        date_from = None
        date_to = None

        try:
            date_from = ranges[0].strip()
            date_to = ranges[1].strip()
            date_from = datetime.datetime.strptime(date_from, '%d.%m.%Y')
            date_to = datetime.datetime.strptime(date_to, '%d.%m.%Y')
        except Exception:
            date_to = None
            date_from = None

        return date_from, date_to

    def clean_username(self):
        phone_number = self.cleaned_data.get('username', '')
        if phone_number:
            return self.remove_non_digits(phone_number)
        
        return ''
    
    def remove_non_digits(self, phone_number):
        # Удаляем все нецифровые символы
        return '+' + re.sub(r'\D', '', phone_number)

    def payment_method_choices(self):
        return (("", "---------"),) + tuple(
            [(src.code, src.name) for src in SourceType.objects.all()]
        )


class OrderSearchForm(forms.Form):
    order_number = forms.CharField(
        required=False, 
        label="Номер заказа",
        widget=forms.TextInput(attrs={
            'placeholder': '100000',
        }),
    )
    partner_point = forms.ChoiceField(
        label="Точка продажи", required=False, choices=()
    )
    username = forms.CharField(
        required=False, 
        label="Телефон клиента", 
        widget=forms.TextInput(attrs={
            'placeholder': '+7 (900) 000-0000',
        }),
    )
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
        ("html", "Показать на сайте"),
        ("csv", "Скачать CSV (Excel)"),
    )
    response_format = forms.ChoiceField(
        widget=forms.RadioSelect,
        required=False,
        choices=format_choices,
        initial="html",
        label="Формат результата",
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
        self.fields["partner_point"].choices = self.partner_choices()
        
        usesrname = kwargs.pop('usesrname', None)
        if usesrname:
            # Форматируем начальное значение перед передачей в поле формы
            self.fields['usesrname'].initial = self.format_phone_number(usesrname)


    def format_phone_number(self, phone_number):
        # Простейший способ форматирования номера телефона
        phone_number = re.sub(r'\D', '', phone_number)  # Удаляем все нецифровые символы
        if len(phone_number) == 11 and phone_number.startswith('7'):
            phone_number = '+7 ({}) {}-{}'.format(
                phone_number[1:4],
                phone_number[4:7],
                phone_number[7:]
            )
        return phone_number
    
    def clean_username(self):
        phone_number = self.cleaned_data.get('username', '')
        if phone_number:
            return self.remove_non_digits(phone_number)
        
        return ''
    
    def remove_non_digits(self, phone_number):
        # Удаляем все нецифровые символы
        return '+' + re.sub(r'\D', '', phone_number)

    def payment_method_choices(self):
        return (("", "---------"),) + tuple(
            [(src.code, src.name) for src in SourceType.objects.all()]
        )

    def partner_choices(self):
        return (("", "Все точки продаж"),) + tuple(
            [(src.code, src.name) for src in Partner.objects.all()]
        )


class ActiveOrderSearchForm(forms.Form):
    partner_point = forms.ChoiceField(
        label="Точка продажи", required=False, choices=()
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

        super().__init__(data, *args, **kwargs)
        self.fields["partner_point"].choices = self.partner_choices()


    def format_phone_number(self, phone_number):
        # Простейший способ форматирования номера телефона
        phone_number = re.sub(r'\D', '', phone_number)  # Удаляем все нецифровые символы
        if len(phone_number) == 11 and phone_number.startswith('7'):
            phone_number = '+7 ({}) {}-{}'.format(
                phone_number[1:4],
                phone_number[4:7],
                phone_number[7:]
            )
        return phone_number
    
    def clean_username(self):
        phone_number = self.cleaned_data.get('username', '')
        if phone_number:
            return self.remove_non_digits(phone_number)
        
        return ''
    
    def remove_non_digits(self, phone_number):
        # Удаляем все нецифровые символы
        return '+' + re.sub(r'\D', '', phone_number)

    def payment_method_choices(self):
        return (("", "---------"),) + tuple(
            [(src.code, src.name) for src in SourceType.objects.all()]
        )

    def partner_choices(self):
        return (("", "Все точки продаж"),) + tuple(
            [(src.code, src.name) for src in Partner.objects.all()]
        )


class OrderNoteForm(forms.ModelForm):
    class Meta:
        model = OrderNote
        fields = ["message"]

    def __init__(self, order, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.order = order
        self.instance.user = user


class ShippingAddressForm(PhoneNumberMixin, forms.ModelForm):
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
    new_status = forms.ChoiceField(label="Новый статус", choices=())

    def __init__(self, order, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set the choices
        choices = [(x, x) for x in order.available_statuses()]
        self.fields["new_status"].choices = choices

    @property
    def has_choices(self):
        return len(self.fields["new_status"].choices) > 0


class NewSourceForm(forms.Form):

    def __init__(self, order, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = order
        self.fields["amount_allocated"].widget.attrs.update({'max': order.total})
        self.fields["amount_allocated"].initial = order.total

    source_type = forms.ChoiceField(
        choices=settings.WEBSHOP_PAYMENT_CHOICES,
        initial=settings.WEBSHOP_PAYMENT_CHOICES[0][0],
        label='Способ оплаты',
        required=True,
        help_text='Выберите для какого способа оплаты создате транзакцию',
    )

    amount_allocated = forms.DecimalField(
        label="Сумма", min_value=0, required=True, help_text='Сумма к оплате'
    )
    payment_id = forms.CharField(max_length=128, label="Код платежа", required=False, help_text='Код оплаты (для интернет транзакций)')
    refund_id = forms.CharField(max_length=128, label="Код возврата", required=False, help_text='Код возврата (для интернет транзакций)')


class NewTransactionForm(forms.ModelForm):

    def __init__(self, order, *args, **kwargs):
        
        super().__init__(*args, **kwargs)

        self.order = order

        txn_type_choices = (('Payment', 'Оплата'), ('Refund', 'Возврат'))
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
        label="Сумма", min_value=0, required=True, help_text='Сумма транзакции'
    )

    code = forms.CharField(max_length=128, label="Код транзакции", required=False, help_text='Код для интернет транзакций. Формат "0e000b000-000f-0000-a000-00000000ac00"')
    paid = forms.BooleanField(initial=True, label="Оплачено", required=True, help_text='Заказ оплачен?')
    refundable = forms.BooleanField(initial=True, label="Возврат возможен?", required=True, help_text='Оплату возможно вернуть?')

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