from django.db import models
from oscar.core.compat import AUTH_USER_MODEL

class AbstractTelegramUser(models.Model):
    """
    Implements the interface declared by shipping.base.Base
    """
    user = models.ForeignKey(
        AUTH_USER_MODEL, verbose_name="Пользователь Сайта", on_delete=models.CASCADE
    )
    telegram_id = models.CharField("ID Телеграм чата", max_length=128)

    is_staff = models.BooleanField(
        "Является сотрудником",
        default=True,
        db_index=True,
        help_text="Показывать эту категорию в результатах поиска и каталогах.",
    )
    
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
    
    def get_user(self):
        return self.user
    
    def set_user(self, user):
        self.user = user
        self.save()


class AbstractTelegramMassage(models.Model):
    """
    Implements the interface declared by shipping.base.Base
    """
    user = models.ForeignKey(
        AUTH_USER_MODEL, verbose_name="Пользователь", on_delete=models.CASCADE
    )
    type = models.CharField("Тип сообщения", max_length=128)
    massage = models.TextField("Описание", blank=True)
    date_sent = models.DateTimeField("Дата отправки", auto_now_add=True)

    class Meta:
        abstract = True
        app_label = "telegram"
        ordering = ["type"]
        verbose_name = "Сообщение Телеграм"
        verbose_name_plural = "Сообщения Телеграм"

    def __str__(self):
        return "%s - %s" % (self.user, self.type)
