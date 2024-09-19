from django.db import models
from oscar.core.compat import AUTH_USER_MODEL

class AbstractTelegramStaff(models.Model):
    """
    Implements the interface declared by shipping.base.Base
    """
    user = models.ForeignKey(
        AUTH_USER_MODEL, verbose_name="Пользователь", on_delete=models.CASCADE
    )
    telegram_id = models.CharField("Тип сообщения", max_length=128)
    
    INFO, WARNING, ERROR = 'info', 'warning', 'error'
    TYPE_CHOICES = (
        ('info', 'Информация'),
        ('warning', 'Предупреждение'),
        ('error', 'Ошибка'),
    )

    type = models.CharField("Тип сообщения", choices=TYPE_CHOICES, max_length=128, default=INFO)

    class Meta:
        abstract = True
        app_label = "telegram"
        ordering = ["user"]
        verbose_name = "Персонал подписанный на Телеграм"
        verbose_name_plural = "Персонал подписанный на Телеграм"

    def __str__(self):
        return "%s - %s" % (self.user, self.type)


class AbstractTelegramMassage(models.Model):
    """
    Implements the interface declared by shipping.base.Base
    """
    user = models.ForeignKey(
        AUTH_USER_MODEL, verbose_name="Пользователь", on_delete=models.CASCADE
    )
    type = models.CharField("Тип сообщения", max_length=128)
    massage = models.TextField("Описание", blank=True)

    class Meta:
        abstract = True
        app_label = "telegram"
        ordering = ["type"]
        verbose_name = "Сообщение Телеграм"
        verbose_name_plural = "Сообщения Телеграм"

    def __str__(self):
        return "%s - %s" % (self.user, self.type)
