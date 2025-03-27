from functools import cached_property

from core import compat
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Group,
    PermissionsMixin,
)
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from .tasks import send_sms_async


class UserManager(BaseUserManager):

    def create_user(self, username, email=None, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and
        password.
        """
        now = timezone.now()
        if not username:
            raise ValueError("Телефон некорректный или пустой.")
        if email:
            email = UserManager.normalize_email(email)

        user = self.model(
            username=username,
            email=email,
            is_staff=False,
            is_active=True,
            is_superuser=False,
            is_email_verified=False,
            last_login=now,
            date_joined=now,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username, email, password, **extra_fields):
        u = self.create_user(username, email, password, **extra_fields)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u


class User(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base user suitable for use in Oscar projects.

    This is basically a copy of the core AbstractUser model but without a
    username field
    """

    username = PhoneNumberField(
        "Номер телефона",
        max_length=12,
        unique=True,
        blank=False,
        db_index=True,
        help_text="Формат телефона: '+7 (900) 000-0000",
    )
    email = models.EmailField("Email", blank=True)
    name = models.CharField("Имя", max_length=255, blank=True)
    telegram_id = models.CharField("Телеграм ID", max_length=255, blank=True)
    is_staff = models.BooleanField(
        "Это сотрудник?",
        default=False,
        db_index=True,
        help_text="Повар, Курьер, Менеджер и т.д.",
    )
    is_active = models.BooleanField(
        "Активен",
        default=True,
        db_index=True,
        help_text="Активен пользователь или нет",
    )
    is_email_verified = models.BooleanField(
        "Email подтвержден",
        default=False,
        help_text="Email подтвержден или нет",
    )
    notification_settings = models.ManyToManyField(
        "user.NotificationSetting",
        verbose_name="Настройки уведомлений",
        related_name="users",
        blank=True,
    )

    date_joined = models.DateTimeField("Дата регистрации", default=timezone.now)
    last_login = models.DateTimeField("Дата последнего входа ", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ("email",)

    class Meta:
        db_table = "auth_user"
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = [
            "username",
            "email",
            "password",
            "name",
            "is_staff",
            "is_active",
            "is_email_verified",
            "date_joined",
            "last_login",
        ]

    def __str__(self):
        name = self.get_full_name()
        if name:
            return name

        return str(self.username)

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the name.
        """
        return self.name.strip()

    def get_img(self):
        """
        Return the user's avatar image.
        """
        name = self.get_full_name()
        return name[0] if name else "А"

    def get_name_and_phone(self):
        name = self.name
        if name:
            return "%s (%s)" % (name, self.username)

        return "%s" % self.username

    def get_staff_name(self):
        staff_profile = self.staff_profile
        if staff_profile:
            staff_name = staff_profile.get_full_name
            staff_role = staff_profile.role.name if staff_profile.role else " - "
            return "%s (%s)" % (staff_name, staff_role)

        name = self.name
        if name:
            return "%s (%s)" % (name, self.username)

        return "%s" % self.username

    @cached_property
    def primary_address(self):
        """
        Returns a user primary shipping address. Usually that will be the
        headquarters or similar..
        """
        address = getattr(self, "address", "")
        if not address:
            return ""
        else:
            return address.line1

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Send an email to this user.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def sms_user(self, message):
        """
        Send an sms to this user.
        """
        if settings.CELERY:
            return send_sms_async.delay(message)
        else:
            return send_sms_async(message)


class NotificationSetting(models.Model):
    ORDER, OFFER, SELL, STATUS, STOCK, TECHNICAL, ERROR = (
        "order",
        "offer",
        "sell",
        "status",
        "stock",
        "technical",
        "error",
    )
    CUSTOMER_CHOICES = (
        (ORDER, "Уведомления о заказах"),
        (OFFER, "Уведомления о персональных акциях и предложениях"),
    )
    CUSTOMER_NOTIF = (ORDER, OFFER)
    STAFF_CHOICES = (
        (SELL, "Уведомления о новых заказах"),
        (STATUS, "Уведомления об изменении статусов заказов"),
        (STOCK, "Уведомления о товарных остатках"),
        (TECHNICAL, "Технические уведомления"),
        (ERROR, "Уведомления об ошибках"),
    )
    STAFF_NOTIF = ("sell", "status", "stock", "technical", "error")
    code = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "auth_notificationsetting"
        verbose_name = "Настройка уведомлений"
        verbose_name_plural = "Настройки уведомлений"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = dict(self.STAFF_CHOICES + self.CUSTOMER_CHOICES).get(self.code, "")
        super().save(*args, **kwargs)


class Staff(models.Model):
    user = models.OneToOneField(
        compat.AUTH_USER_MODEL,
        related_name="staff_profile",
        on_delete=models.CASCADE,
        null=True,
    )
    first_name = models.CharField("Имя", blank=False, null=True, max_length=255)
    last_name = models.CharField("Фамилия", blank=True, null=True, max_length=255)
    middle_name = models.CharField("Отчество", blank=True, null=True, max_length=255)
    role = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="staffs",
        verbose_name="Должность",
        null=True,
    )
    MALE, FEMALE = "М", "Ж"
    gender_choices = ((MALE, "Мужчина"), (FEMALE, "Женщина"))
    gender = models.CharField(
        max_length=1, choices=gender_choices, verbose_name="Пол", null=True, blank=True
    )
    date_of_birth = models.DateField(
        verbose_name="Дата рождения", null=True, blank=True
    )
    evotor_id = models.CharField("ID Эвотор", max_length=128, null=True, blank=True)
    is_active = models.BooleanField(
        "Активен",
        default=True,
        db_index=True,
        help_text="Активен сотрудник или нет",
    )

    @staticmethod
    def get_role_choices():
        groups = Group.objects.all()
        return [(group.id, group.name) for group in groups]

    def get_user(self):
        return self.user

    def set_user(self, user):
        self.user = user
        self.save()

    def has_permission(self):
        return self.is_active

    def __str__(self):
        return "%s - %s %s" % (self.user, self.last_name, self.first_name)

    @property
    def get_role(self):
        return self.role if self.role else "Не задана"

    @property
    def get_full_name(self):
        name_parts = filter(None, [self.last_name, self.first_name, self.middle_name])
        name = " ".join(name_parts).strip()
        return name if name else "ФИО не указаны"

    class Meta:
        db_table = "auth_staff"
        permissions = (("full_access", "Полный доступ ко всему сайту"),)
        verbose_name = "Персонал"
        verbose_name_plural = "Персонал"
