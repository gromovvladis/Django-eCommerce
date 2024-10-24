from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from phonenumber_field.modelfields import PhoneNumberField
from oscar.core import compat
from django.contrib.auth.models import Group


class Staff(models.Model):
    """
    Dummy profile model used for testing
    """
    user = models.OneToOneField(compat.AUTH_USER_MODEL, related_name="profile",
                                on_delete=models.CASCADE)

    last_name = models.CharField("Фамилия", blank=False, null=False, max_length=255)
    first_name = models.CharField("Имя", blank=False, null=False, max_length=255)
    middle_name = models.CharField("Отчество", blank=True, null=False, max_length=255)

    role = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="staffs",
        verbose_name="Должность",
        null=True,
    )

    MALE, FEMALE = 'М', 'Ж'
    gender_choices = (
        (MALE, 'Мужчина'), 
        (FEMALE, 'Женщина'))
    gender = models.CharField(max_length=1, choices=gender_choices,
                              verbose_name='Пол', null=True, blank=True)
    age = models.PositiveIntegerField(verbose_name='Возраст', null=True, blank=True)

    image = models.ImageField(blank=True, null=True, verbose_name='Фото', upload_to="profile")

    telegram_id = models.CharField("ID Телеграм чата", max_length=128, null=True, blank=True)
    evotor_id = models.CharField("ID Телеграм чата", max_length=128, null=True, blank=True)

    is_active = models.BooleanField(
        "Активен",
        default=True,
        db_index=True,
        help_text="Активен сотрудник или нет",
    )

    NEW, STATUS, TECHNICAL, OFF = 'new-order', 'status-order', 'technical', 'off'
    NOTIF_CHOICES = (
        ('new-order', 'Только уведомления о новых заказах'),
        ('status-order', 'Уведомления об изменении заказов и новых заказах'),
        ('technical', 'Технические уведомления'),
        ('off', 'Отключить уведомления'),
    )

    notif = models.CharField("Уведомления", choices=NOTIF_CHOICES, max_length=128, default=NEW, db_index=True)

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
        name = f"{self.last_name} {self.first_name} {self.middle_name}".strip()
        return name if name else "ФИО не указаны"
    
    class Meta:
        db_table = "auth_staff"
        permissions = (
            ("full_access", "Полный доступ ко всему сайту"),   
        )
        verbose_name = "Персонал"
        verbose_name_plural = "Персонал"


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
        "Email verified",
        default=False,
        help_text="Email подтвержден или нет",
    )
    
    ORDER, OFFER, OFF = 'order', 'offer', 'off'
    NOTIF_CHOICES = (
        ('order', 'Только уведомления о заказах'),
        ('offer', 'Уведомления об персональных акциях и предложениях'),
        ('off', 'Отключить уведомления'),
    )

    notif = models.CharField("Уведомления", choices=NOTIF_CHOICES, max_length=128, default=ORDER, db_index=True)
    
    date_joined = models.DateTimeField("Дата регистрации", default=timezone.now)
    last_login = models.DateTimeField("Дата последнего входа ", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "auth_user"
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["username", 
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
        return name[0] if name else 'А'

    def get_name_and_phone(self):
        name = self.name
        if name:
            return "%s (%s)" % (name, self.username)
        
        return "%s" % self.username 
    
    def get_staff_name(self):
        staff_profile = self.profile
        if staff_profile:
            staff_name = staff_profile.get_full_name
            staff_role = staff_profile.role.name if staff_profile.role else " - "
            return "%s (%s)" % (staff_name, staff_role)
        
        name = self.name
        if name:
            return "%s (%s)" % (name, self.username)
        
        return "%s" % self.username
        
    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Send an email to this user.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def sms_user(self, subject, message, from_email=None, **kwargs):
        """
        Send an email to this user.
        """
        pass

    # def _migrate_alerts_to_user(self):
    #     """
    #     Transfer any active alerts linked to a user's email address to the
    #     newly registered user.
    #     """
    #     # pylint: disable=no-member
    #     ProductAlert = self.alerts.model
    #     alerts = ProductAlert.objects.filter(
    #         email=self.email, status=ProductAlert.ACTIVE
    #     )
    #     alerts.update(user=self, key="", email="")

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
        # Migrate any "anonymous" product alerts to the registered user
        # Ideally, this would be done via a post-save signal. But we can't
        # use get_user_model to wire up signals to custom user models
        # see Oscar ticket #1127, Django ticket #19218
        # self._migrate_alerts_to_user()
