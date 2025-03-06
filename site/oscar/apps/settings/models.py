from django.db import models
from django.contrib.auth.models import Group


class Settings(models.Model):
    auth = models.CharField(
        verbose_name="Название сайта",
        null=False,
        blank=False,
        max_length=255,
        help_text="Пример: Доставка суши и роллов | Сайт Москва",
    )
    AUTH_PHONE, AUTH_EMAIL = (
        "oscar.apps.user.auth_backends.PhoneBackend",
        "oscar.apps.user.auth_backends.PhoneBackend",
    )
    auth_choises = (
        (AUTH_PHONE, "Телефон"),
        (AUTH_EMAIL, "Электронная почта"),
    )
    auth = models.CharField(
        verbose_name="Аунтификация",
        choices=auth_choises,
        null=False,
        blank=False,
        default=AUTH_EMAIL,
        max_length=255,
    )
    sms_provider = models.CharField(
        verbose_name="СМС имя провайдера",
        null=True,
        blank=True,
        max_length=255,
        help_text="Имя с которого будует отсылаться СМС",
    )
    sms_debug = models.BooleanField(
        verbose_name="Тестирование СМС",
        null=False,
        blank=False,
        default=False,
        max_length=255,
        help_text="Если значение положительное, то смс не высылаются. Для входа на сайт подходит код: 1111",
    )
    sms_auth_login = models.CharField(
        verbose_name="SMSAERO логин",
        null=True,
        blank=True,
        max_length=255,
        help_text="Электронная почта аккаунта SMSAERO",
    )
    sms_auth_token = models.CharField(
        verbose_name="SMSAERO API токен",
        null=True,
        blank=True,
        max_length=255,
        help_text="Ключ полученый при регистрации",
    )
    payments = models.ManyToManyField(
        "settings.PaymentSettings",
        verbose_name="Способы оплаты",
        related_name="settings",
        blank=True,
    )
    yoomoney_id = models.CharField(
        verbose_name="ID аккаунта ЮКасса",
        null=True,
        blank=True,
        max_length=255,
    )
    yoomoney_key = models.CharField(
        verbose_name="Секретный ключ аккаунта ЮКасса",
        null=True,
        blank=True,
        max_length=255,
    )
    COMMON, USN_DOHOD, USN_RASHOD, ENVD, ESN, PATENT = 0, 1, 2, 3, 4, 5
    tax_choises = (
        (COMMON, "Общая система налогообложения"),
        (USN_DOHOD, "Упрощенная (УСН, доходы)"),
        (USN_RASHOD, "Упрощенная (УСН, доходы минус расходы)"),
        (ENVD, "Единый налог на вмененный доход (ЕНВД)"),
        (ESN, "Единый сельскохозяйственный налог (ЕСН)"),
        (PATENT, "Патентная система налогообложения"),
    )
    tax_system = models.CharField(
        verbose_name="Система налогообложения",
        max_length=1,
        null=True,
        blank=True,
        choices=tax_choises,
        default=0,
    )
    delivery_available = models.BooleanField(
        "Доставка",
        default=False,
        help_text="Магазин осуществляет доставку?",
    )
    delivery_api_key = models.CharField(
        verbose_name="Ключ API карт",
        null=True,
        blank=True,
        max_length=255,
        help_text="API ключ Яндекс, 2ГИС или DaData",
    )
    store_select = models.BooleanField(
        "Несколько магазинов",
        default=False,
        help_text="Если значение положительное, то клиентам доступен выбор магазина, и корзина может содержать товары одновременно только из одного выбранного магазина",
    )
    store_default = models.ForeignKey(
        "store.Store",
        null=True,
        blank=True,
        verbose_name="Основной магазин",
        on_delete=models.SET_NULL,
        help_text="Данный магазин используется, если клиент еще не выбрал магазин",
    )
    analytics_google = models.CharField(
        verbose_name="ID Google аналитики",
        null=True,
        blank=False,
        max_length=255,
    )
    analytics_yandex = models.CharField(
        verbose_name="ID Яндекс аналитики",
        null=True,
        blank=True,
        max_length=255,
    )

    class Meta:
        verbose_name = "Настройки"
        verbose_name_plural = "Настройки"


class PaymentSettings(models.Model):
    YOOMONEY, ELECTRON, CASH, CASH_RECEIVE = (
        "YOOMONEY",
        "ELECTRON",
        "CASH",
        "CASH_RECEIVE",
    )
    PAYMENT_CHOICES = (
        ("YOOMONEY", "Картой онлайн"),
        ("ELECTRON", "Картой в магазине"),
        ("CASH", "Наличными в магазине"),
        ("CASH_RECEIVE", "Наличными при получении"),
    )
    code = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Способ оплаты"
        verbose_name_plural = "Способы оплаты"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = dict(self.PAYMENT_CHOICES).get(self.code, "")
        super().save(*args, **kwargs)
