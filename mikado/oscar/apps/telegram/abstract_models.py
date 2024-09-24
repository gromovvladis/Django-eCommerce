from django.db import models
from oscar.core.compat import AUTH_USER_MODEL

class AbstractTelegramMessage(models.Model):
    """
    Implements the interface declared by shipping.base.Base
    """
    user = models.ForeignKey(
        AUTH_USER_MODEL, verbose_name="Пользователь Сайта", on_delete=models.CASCADE
    )

    NEW, STATUS, TECHNICAL, OFFER, MISC = 'new-order', 'status-order', 'technical', 'offer', 'misc'
    TYPE_CHOICES = (
        ('new-order', 'Уведомление о новом заказе'),
        ('status-order', 'Уведомление об изменении статуса заказа'),
        ('technical', 'Техническое уведомление'),
        ('offer', 'Уведомление о персональном предложении'),
        ('misc', 'Без типа'),
    )
    type = models.CharField("Тип сообщения", max_length=128, choices=TYPE_CHOICES, default=MISC)

    message = models.TextField("Описание", blank=True)
    date_sent = models.DateTimeField("Дата отправки", auto_now_add=True)

    class Meta:
        abstract = True
        app_label = "telegram"
        ordering = ["type"]
        verbose_name = "Сообщение Телеграм"
        verbose_name_plural = "Сообщения Телеграм"

    def __str__(self):
        return "%s - %s" % (self.user, self.type)
