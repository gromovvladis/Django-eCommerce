from phonenumber_field.modelfields import PhoneNumberField

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..utils import random_code, valid_to, resend_at
from ..conf import conf


class SMSMessage(models.Model):
    """
    Save sended sms after as history
    """

    created = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField("Phone number", max_length=20)
    cost = models.DecimalField("Cost", decimal_places=2, max_digits=12, null=True)

    def __str__(self):
        return f"{self.phone_number} / {self.created}"

    def __repr__(self):
        return f"{self.phone_number}"

    class Meta:
        verbose_name = "Отправленное СМС"
        verbose_name_plural = "Отправленные СМС"


class PhoneCode(models.Model):
    """
    After validation save phone code instance
    """

    phone_number = PhoneNumberField(unique=True)
    owner = models.ForeignKey(get_user_model(), null=True, on_delete=models.CASCADE)
    code = models.PositiveIntegerField(default=random_code)
    valid_to = models.DateTimeField(default=valid_to)
    resend_at = models.DateTimeField(default=resend_at)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "СМС код аутентификации"
        verbose_name_plural = "СМС коды аутентификации"

    def __str__(self):
        return f"{self.phone_number} ({self.code})"

    def __repr__(self):
        return self.__str__()

    @property
    def is_allow(self):
        return timezone.now() >= self.valid_to

    @property
    def is_resend_allow(self):
        return timezone.now() >= self.resend_at

    @property
    def message(self) -> str:
        return " ".join((str(conf.SMS_AUTH_MESSAGE), str(self.code)))

    def save(self, *args, **kwargs):
        from ..conf import conf

        pretendent = self.__class__.objects.filter(
            phone_number=self.phone_number
        ).first()
        if pretendent is not None:
            self.pk = pretendent.pk

        if conf.SMS_AUTH_DEBUG_PHONE_NUMBER is not None:
            if self.phone_number == conf.SMS_AUTH_DEBUG_PHONE_NUMBER:
                self.code = conf.SMS_DEBUG_CODE

        super().save(*args, **kwargs)
