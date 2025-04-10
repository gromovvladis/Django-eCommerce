import logging

import phonenumbers
from core.compat import get_user_model
from core.forms.widgets import DatePickerInput
from core.loading import get_model
from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.utils.http import url_has_allowed_host_and_scheme
from phonenumber_field.phonenumber import PhoneNumber

User = get_user_model()
Staff = get_model("user", "Staff")
NotificationSetting = get_model("user", "NotificationSetting")

logger = logging.getLogger("apps.webshop.user")


class UserSearchForm(forms.Form):
    username = forms.CharField(required=False, label="Номер телефона")
    name = forms.CharField(required=False, label="Имя клиента")


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
        required=True,
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
        label="Пол", choices=Staff.gender_choices, required=False
    )
    is_active = forms.BooleanField(
        label="Активен",
        initial=True,
        required=True,
        help_text="Активен сотрудник или нет",
    )
    date_of_birth = forms.DateField(
        label="Дата рождения", required=False, widget=DatePickerInput
    )
    notifications = forms.MultipleChoiceField(
        label="Уведомления Телеграм",
        required=False,
        choices=NotificationSetting.STAFF_CHOICES,
        help_text="Уведомления будут поступать только из магазина, в котором пользователь отмечен как сотрудник.",
    )
    # evotor_update = forms.BooleanField(
    #     label="Эвотор",
    #     required=False,
    #     initial=True,
    #     help_text="Синхронизировать с Эвотор",
    # )
    redirect_url = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Staff
        fields = (
            "username",
            "last_name",
            "first_name",
            "middle_name",
            "role",
            "gender",
            "date_of_birth",
            "is_active",
        )
        sequence = (
            "username",
            "last_name",
            "first_name",
            "middle_name",
            "role",
            "gender",
            "date_of_birth",
            "is_active",
        )
        # widgets = {
        #     'evotor_update': forms.CheckboxInput(attrs={
        #         'class' : 'checkbox-ios-switch',
        #     }),
        # }

    def __init__(self, store=None, *args, **kwargs):
        self.store = store
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = Staff.get_role_choices()
        # self.fields["evotor_update"].initial = self.request.COOKIES.get("evotor_update", True) == "True"
        if self.instance and self.instance.pk:
            self.fields["notifications"].initial = list(
                self.instance.notifications.values_list("code", flat=True)
            )
            if self.instance.user:
                self.fields["username"].initial = self.instance.user.username

    def clean_redirect_url(self):
        url = self.cleaned_data["redirect_url"].strip()
        if url and url_has_allowed_host_and_scheme(url, self.host):
            return url
        return settings.LOGIN_REDIRECT_URL

    def clean_role(self):
        # Получаем значение роли
        role_id = self.cleaned_data.get("role")
        if role_id:
            try:
                return Group.objects.get(id=role_id)
            except Group.DoesNotExist:
                raise forms.ValidationError("Выбранная роль не существует.")
        return None

    def clean_notifications(self):
        """
        Обрабатывает уведомления:
        - Проверяет, что коды уведомлений корректны.
        - Создает объекты NotificationSetting, если они не существуют.
        - Возвращает список объектов NotificationSetting.
        """
        notifications = self.cleaned_data.get("notifications", [])
        valid_notifications = []
        for code in notifications:
            if code in NotificationSetting.STAFF_NOTIF:
                notification, _ = NotificationSetting.objects.get_or_create(code=code)
                valid_notifications.append(notification)
            else:
                raise forms.ValidationError(f"Недопустимый код уведомления: {code}")

        return valid_notifications

    def clean_username(self):
        number = self.cleaned_data.get("username")
        try:
            username = PhoneNumber.from_string(number, region="RU")
            if not username.is_valid():
                self.add_error("username", "Это недопустимый формат телефона.")
        except phonenumbers.NumberParseException:
            self.add_error(
                "username",
                "Это недействительный формат телефона.",
            )
            return number

        return username

    def _update_user_groups(self, user, role):
        """Обновляет группы пользователя на основе выбранной роли."""
        if role:
            user.groups.set([role])
        else:
            user.groups.clear()

    def _update_staff_notifications(self, user, notifications):
        """Обновляет уведомления сотрудника."""
        user.notification_settings.set(notifications)

    def save(self, commit=True):
        username = self.cleaned_data.get("username")
        user, _ = User.objects.get_or_create(username=username)
        user.is_staff = True

        if self.store:
            self.store.users.add(user)

        staff = self.instance if self.instance.pk else Staff(user=user)
        staff.user = user
        staff.first_name = self.cleaned_data.get("first_name", staff.first_name)
        staff.last_name = self.cleaned_data.get("last_name", staff.last_name)
        staff.middle_name = self.cleaned_data.get("middle_name", staff.middle_name)
        staff.gender = self.cleaned_data.get("gender", staff.gender)
        staff.is_active = self.cleaned_data.get("is_active", staff.is_active)
        staff.date_of_birth = self.cleaned_data.get(
            "date_of_birth", staff.date_of_birth
        )

        # Обновляем группы пользователя
        role = self.cleaned_data.get("role")
        self._update_user_groups(user, role)

        # Обновляем уведомления сотрудника
        notifications = self.cleaned_data.get("notifications")
        self._update_staff_notifications(user, notifications)

        if commit:
            staff.save()
            user.save()

        # evotor_update = self.cleaned_data.get("evotor_update")
        # if evotor_update:
        #     try:
        #         if created or not staff.evotor_id:
        #             staff, error = EvatorCloud().create_evotor_staff(staff)
        #             if error:
        #                 messages.warning(self.request, error)
        #     except Exception as e:
        #         logger.error(
        #             "Ошибка при отправке созданного / измененного пользователя в Эвотор. Ошибка %s",
        #             e,
        #         )

        return staff


class GroupForm(forms.ModelForm):
    """ "
    товары / catalogue +
       полный доступ / product.full_access
       просматривать / product.read
       изменять наличие и цену / product.change_price_and_stockrecord
       изменять наличие / product.change_stockrecord

    заказы / order +
       полный доступ / order.full_access
       просматривать / order.read
       изменять / order.update_order
       удалять / order.remove_order

    доставка / shipping
       полный доступ / shipping.full_access
       просматривать / shipping.read
       изменять доставки / shipping.change_shipping

    оплата / payment +
       полный доступ / payment.full_access
       просматривать / payment.read
       изменять платежи / payment.make_refund

    Магазины / store +
       полный доступ / staff.full_access

    клиенты /user +
       полный доступ / staff.full_access

    скидки / offer +
       полный доступ / staff.full_access

    црм / evotor +
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
        required=False,
    )

    class Meta:
        model = Group
        fields = ("name", "permissions")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        permissions = Permission.objects.filter(
            codename__in=[
                "full_access",
                "read",
                "update_shipping",
                "update_stockrecord",
                "update_order",
                "make_refund",
                "remove_order",
            ]
        )

        # Словарь для хранения сгруппированных разрешений по приложениям
        grouped_permissions = {}

        # Группируем разрешения по приложениям
        for permission in permissions:
            app_label = self.get_app_verbose_name(permission.content_type.app_label)
            if app_label not in grouped_permissions:
                grouped_permissions[app_label] = []
            grouped_permissions[app_label].append((permission.id, permission.name))

        # Преобразуем сгруппированные разрешения в формат для виджета
        self.fields["permissions"].choices = [
            (app_label, grouped_permissions[app_label])
            for app_label in grouped_permissions
        ]

        # Устанавливаем queryset для permissions
        self.fields["permissions"].queryset = permissions

    def get_app_verbose_name(self, app_label):
        try:
            app_config = apps.get_app_config(app_label)
            return app_config.verbose_name
        except LookupError:
            return app_label
