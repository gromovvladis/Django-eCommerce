import phonenumbers

from django import forms
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.utils.http import url_has_allowed_host_and_scheme

from phonenumber_field.phonenumber import PhoneNumber

from oscar.core.compat import get_user_model
from oscar.core.loading import get_model

User = get_user_model()
Staff = get_model("user", "Staff")


class UserSearchForm(forms.Form):
    username = forms.CharField(required=False, label="Номер телефона")
    name = forms.CharField(required=False, label="Имя пользователя")


class StaffForm(forms.ModelForm):
    
    username = forms.CharField(
        label="Номер телефона",
        required=True,
        help_text="Номер телефона пользователя в формате +7 (900) 000-0000",
    )
    last_name = forms.CharField(
        label="Фамилия",
        required=False,
        help_text="Фамилия сотрудника. Пример: 'Иванов'",
        )
    first_name = forms.CharField(
        label="Имя",
        required=False,
        help_text="Имя сотрудника. Пример: 'Иван'",
    )
    middle_name = forms.CharField(
        label="Отчество",
        required=False,
        help_text="Отчество сотрудника. Пример: 'Иванович'. Необязательно",
    )
    role = forms.ChoiceField(
        label="Должность",
        choices=[],
        required=False,
        help_text="Курьер, Менеджер, Сотрудник кухни и т.д. Определяет доступ в панели упарвления",
    )
    gender = forms.ChoiceField(
        label="Пол",
        choices=Staff.gender_choices, 
        required=False
    )
    is_active = forms.BooleanField(
        label="Активен",
        initial=True,
        required=True,
        help_text="Активен сотрудник или нет",
    )
    age = forms.IntegerField(label="Возраст", required=False)
    image = forms.ImageField(label="Фото", required=False)

    error_messages = {
        "invalid_login": "Пожалуйста, введите корректный номер телефона.",
        "inactive": "Этот аккаунт не активен.",
    }
    redirect_url = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Staff
        fields = ('username', 'last_name', 'first_name', 'middle_name', 'role', 'gender', 'is_active', 'age', 'image')
        sequence = (
            "username",
            "last_name",
            "first_name",
            "middle_name",
            "role",
            "gender",
            "is_active",
            "age",
            "image",
        )

    def __init__(self, partner=None, *args, **kwargs):
        self.partner = partner
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = Staff.get_role_choices()

    def clean_redirect_url(self):
        url = self.cleaned_data["redirect_url"].strip()
        if url and url_has_allowed_host_and_scheme(url, self.host):
            return url
        return settings.LOGIN_REDIRECT_URL
    
    def clean_role(self):
        # Получаем значение роли
        role_id = self.cleaned_data.get('role')
        if role_id:
            try:
                return Group.objects.get(id=role_id)
            except Group.DoesNotExist:
                raise forms.ValidationError("Выбранная роль не существует.")
        return None
    
    def clean_username(self):
        number = self.cleaned_data.get("username")

        try:
            username = PhoneNumber.from_string(number, region='RU')
            if not username.is_valid():
                self.add_error(
                    "username", "Это недопустимый формат телефона."
                )
        except phonenumbers.NumberParseException:
            self.add_error(
                "username", "Это недействительный формат телефона.",
            )
            return number

        return username

    def save(self, commit=True):
        username = self.cleaned_data.get("username", None)
        user, created = User.objects.get_or_create(username=username)
        user.is_staff = True
        user.save()
        if self.partner:
            self.partner.users.add(user)

        staff = Staff.objects.create(
            user=user,
            first_name=self.cleaned_data.get('first_name', ''),
            last_name=self.cleaned_data.get('last_name', ''),
            middle_name=self.cleaned_data.get('middle_name', ''),
            role=self.cleaned_data.get('role', ''),
            gender=self.cleaned_data.get('gender', ''),
            is_active=self.cleaned_data.get('is_active', False),
            age=self.cleaned_data.get('age', None),
            image=self.cleaned_data.get('image', None)
        )

        return staff


class GroupForm(forms.ModelForm):
    """"
    товары / product +
       полный доступ / product.full_access
       просматривать / product.read
       изменять наличие / product.change_stockrecord
        
    заказы / order +
       полный доступ / order.full_access
       просматривать / order.read
       изменять / order.change_order
       изменять статус / order.change_order_status
       изменять оплату / order.change_order_payment

    доставка / partner
       полный доступ / delivery.full_access
       просматривать / delivery.read
       изменять доставки / delivery.change_delivery

    оплата / payment +
       полный доступ / payment.full_access
       просматривать / payment.read
       изменять платежи / payment.make_refund

    точки продажи / partner +
       полный доступ / staff.full_access

    клиенты /user +
       полный доступ / staff.full_access

    скидки / offer +
       полный доступ / staff.full_access

    црм / crm +
       полный доступ / staff.full_access

    телеграм / telegram +
       полный доступ / staff.full_access

    контент / page +
       полный доступ / staff.full_access

    отчеты / report +
       полный доступ / staff.full_access
    """

    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Получаем все разрешения из базы данных один раз
        permissions = Permission.objects.select_related('content_type').filter(
            content_type__app_label__in=[
                'group',
                'address',
                'shipping',
                'delivery',
                'catalogue',
                'communication',
                'reviews',
                'user',
                'voucher',
                'home',
                'offer',
                'order',
                'partner',
                'payment',
            ]
        )



        # Словарь для хранения сгруппированных разрешений по приложениям
        grouped_permissions = {}
        
        # Группируем разрешения по приложениям
        for permission in permissions:
            app_label = permission.content_type.app_label
            if app_label not in grouped_permissions:
                grouped_permissions[app_label] = []
            grouped_permissions[app_label].append((permission.id, permission.name))
        
        # Преобразуем сгруппированные разрешения в формат для виджета
        self.fields['permissions'].choices = [
            (app_label, grouped_permissions[app_label]) for app_label in grouped_permissions
        ]
        
        # Устанавливаем queryset для permissions
        self.fields['permissions'].queryset = permissions


   




# class GroupForm(forms.ModelForm):
#     class Meta:
#         model = Group
#         fields = ['name', 'permissions']
#         widgets = {
#             'permissions': forms.CheckboxSelectMultiple,  # Используем чекбоксы для выбора разрешений
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['permissions'].queryset = Permission.objects.all()  


#             # Обработка доступа для пользователя с ограниченным доступом
#             # dashboard_access_perm = [Permission.objects.get(codename="dashboard_access", content_type__app_label="partner")]

#             # access_permissions = {
#             #     "product_access": {
#             #         "all": Permission.objects.filter(content_type__app_label="catalogue"),
#             #         "view": [Permission.objects.get(codename="view_productrecord", content_type__app_label="catalogue")]
#             #     },
#             #     "stock_access": {
#             #         "all": Permission.objects.filter(content_type__app_label="stockrecord"),
#             #         "view": [Permission.objects.get(codename="view_stockrecord", content_type__app_label="stockrecord")]
#             #     },
#             #     "orders_access": {
#             #         "all": Permission.objects.filter(content_type__app_label="order"),
#             #         "view": [Permission.objects.get(codename="view_order", content_type__app_label="order")]
#             #     },
#             #     "promo_access": {
#             #         "all": Permission.objects.filter(content_type__app_label="home") | Permission.objects.filter(content_type__app_label="offer"),
#             #         "view": [
#             #             Permission.objects.get(codename="view_promocategory", content_type__app_label="home"),
#             #             Permission.objects.get(codename="view_action", content_type__app_label="home"),
#             #             Permission.objects.get(codename="view_benefit", content_type__app_label="offer"),
#             #             Permission.objects.get(codename="view_condition", content_type__app_label="offer"),
#             #             Permission.objects.get(codename="view_conditionaloffer", content_type__app_label="offer"),
#             #         ]
#             #     },
#             #     # Добавьте аналогичные структуры для других категорий доступа
#             # }

#             # for key, value in access_permissions.items():
#             #     access_level = self.cleaned_data.get(key, "no")
#             #     if access_level in value:
#             #         dashboard_access_perm.extend(value[access_level])

#             # # Добавляем разрешения пользователю
#             # user.user_permissions.set(dashboard_access_perm, clear=True)

#     # def save(self, commit=True):
    


# ----------------------------------------------------------------



    # PRODUCTS = (
    #     ("view", "Доступ к просмотру товаров"),
    #     ("all", "Доступ к редактированию товаров"),
    #     ("no", "Нет доступа к товарам"),
    # )
    # product_access = forms.ChoiceField(
    #     choices=PRODUCTS,
    #     widget=forms.RadioSelect,
    #     label="Доступ к товарам",
    #     initial="no",
    # )

    # STOCK = (
    #     ("view", "Доступ к просмотру товарных записей"),
    #     ("all", "Доступ к редактированию товарных записей"),
    #     ("no", "Нет доступа к товарным записям"),
    # )
    # stock_access = forms.ChoiceField(
    #     choices=STOCK,
    #     widget=forms.RadioSelect,
    #     label="Доступ к товарным записям (наличие товара и количество товара)",
    #     initial="no",
    # )

    # ORDERS = (
    #     ("view", "Доступ к просмотру заказов"),
    #     ("all", "Доступ к редактированию заказов"),
    #     ("no", "Нет доступа к заказам"),
    # )
    # orders_access = forms.ChoiceField(
    #     choices=ORDERS,
    #     widget=forms.RadioSelect,
    #     label="Доступ к заказам",
    #     initial="no",
    # )

    # PROMO = (
    #     ("view", "Доступ к просмотру акций и промо-товаров"),
    #     ("all", "Доступ к редактированию акций и промо-товаров"),
    #     ("no", "Нет доступа к акциям и промо-товарам"),
    # )
    # promo_access = forms.ChoiceField(
    #     choices=ROLE_CHOICES,
    #     widget=forms.RadioSelect,
    #     label="Доступ к акциям и промо-товарам",
    #     initial="no",
    # )

    # USERS = (
    #     ("view", "Доступ к просмотру пользователей"),
    #     ("all", "Доступ к редактированию пользователей"),
    #     ("no", "Нет доступа к пользователям"),
    # )
    # users_access = forms.ChoiceField(
    #     choices=USERS,
    #     widget=forms.RadioSelect,
    #     label="Доступ к пользователям",
    #     initial="no",
    # )

    # PAYMENTS = (
    #     ("view", "Доступ к просмотру платежей"),
    #     ("all", "Доступ к редактированию платежей"),
    #     ("no", "Нет доступа к платежам"),
    # )
    # payments_access = forms.ChoiceField(
    #     choices=PAYMENTS,
    #     widget=forms.RadioSelect,
    #     label="Доступ к платежам",
    #     initial="no",
    # )

    # DELIVERY = (
    #     ("view", "Доступ к просмотру доставок"),
    #     ("all", "Доступ к редактированию доставок"),
    #     ("no", "Нет доступа к доставкам"),
    # )
    # delivery_access = forms.ChoiceField(
    #     choices=DELIVERY,
    #     widget=forms.RadioSelect,
    #     label="Доступ к доставкам",
    #     initial="no",
    # )


# ----------------------------------------------------------------

    #     staff = self.cleaned_data.get("staff", "limited")
    #     user = super().save(commit=False)
    #     role = self.cleaned_data.get("role", "limited")
    #     user.is_staff = role == "staff"
    #     user.save()
    #     self.partner.users.add(user)
    #     if staff:
    #         # Если это сотрудник, создаем профиль
    #         Profile.objects.create(
    #             user=user,
    #             first_name=self.cleaned_data.get('first_name', ''),
    #             last_name=self.cleaned_data.get('last_name', ''),
    #             middle_name=self.cleaned_data.get('middle_name', ''),
    #             job=self.cleaned_data.get('job', ''),
    #             gender=self.cleaned_data.get('gender', ''),
    #             age=self.cleaned_data.get('age', None),
    #             image=self.cleaned_data.get('image', None)
    #         )

    #         if role == "limited":
    #             product_access = self.cleaned_data.get("product_access", "no")
    #             stock_access = self.cleaned_data.get("stock_access", "no")
    #             orders_access = self.cleaned_data.get("orders_access", "no")
    #             promo_access = self.cleaned_data.get("promo_access", "no")
    #             users_access = self.cleaned_data.get("users_access", "no")
    #             payments_access = self.cleaned_data.get("payments_access", "no")
    #             delivery_access = self.cleaned_data.get("delivery_access", "no")

    #             dashboard_access_perm = []
    #             dashboard_access_perm.append(Permission.objects.get(
    #                 codename="dashboard_access", content_type__app_label="partner"
    #             ))

    #             if product_access == "all":
    #                 dashboard_access_perm.append(Permission.objects.filter(content_type__app_label="catalogue"))
    #             elif product_access == "view":
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_productrecord", content_type__app_label="catalogue"
    #                 ))

    #             if stock_access == "all":
    #                 dashboard_access_perm.append(Permission.objects.filter(content_type__app_label="stockrecord"))
    #             elif stock_access == "view":
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_stockrecord", content_type__app_label="stockrecord"
    #                 ))

    #             if orders_access == "all":
    #                 dashboard_access_perm.append(Permission.objects.filter(content_type__app_label="order"))
    #             elif orders_access == "view":
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_order", content_type__app_label="order"
    #                 ))

    #             if promo_access == "all":
    #                 dashboard_access_perm.append(Permission.objects.filter(content_type__app_label="home"))
    #                 dashboard_access_perm.append(Permission.objects.filter(content_type__app_label="offer"))
    #             elif promo_access == "view":
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_promocategory", content_type__app_label="home"
    #                 ))
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_action", content_type__app_label="home"
    #                 ))
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_benefit", content_type__app_label="offer"
    #                 ))
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_condition", content_type__app_label="offer"
    #                 ))
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_conditionaloffer", content_type__app_label="offer"
    #                 ))


    #             if users_access == "all":
    #                 dashboard_access_perm.append(Permission.objects.filter(content_type__app_label="user"))
    #             elif users_access == "view":
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_user", content_type__app_label="user"
    #                 ))
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_useraddress", content_type__app_label="user"
    #                 ))
                

    #             if payments_access == "all":
    #                 dashboard_access_perm.append(Permission.objects.filter(content_type__app_label="payment"))
    #             elif payments_access == "view":
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_paymentevent", content_type__app_label="payment"
    #                 ))
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_paymenteventtype", content_type__app_label="payment"
    #                 ))
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_paymenteventquantity", content_type__app_label="payment"
    #                 ))
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_source", content_type__app_label="payment"
    #                 ))
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_sourcetype", content_type__app_label="payment"
    #                 ))
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_transaction", content_type__app_label="payment"
    #                 ))
                

    #             if delivery_access == "all":
    #                 dashboard_access_perm.append(Permission.objects.filter(content_type__app_label="delivery"))
    #             elif delivery_access == "view":
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_deliveryorder", content_type__app_label="delivery"
    #                 ))
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_deliveryzona", content_type__app_label="delivery"
    #                 ))
    #                 dashboard_access_perm.append(Permission.objects.get(
    #                     codename="view_deliverysession", content_type__app_label="delivery"
    #                 ))
                

    #             user.user_permissions.add(dashboard_access_perm)
                
    #     return user



# class ProductAlertUpdateForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         alert = kwargs["instance"]
#         if alert.user:
#             # Remove 'unconfirmed' from list of available choices when editing
#             # an alert for a real user
#             choices = self.fields["status"].choices
#             del choices[0]
#             self.fields["status"].choices = choices

#     class Meta:
#         model = ProductAlert
#         fields = [
#             "status",
#         ]


# class ProductAlertSearchForm(forms.Form):
#     STATUS_CHOICES = (("", "------------"),) + ProductAlert.STATUS_CHOICES

#     status = forms.ChoiceField(
#         required=False, choices=STATUS_CHOICES, label="Статус"
#     )
#     name = forms.CharField(required=False, label="Имя")
#     email = forms.EmailField(required=False, label="Email")
