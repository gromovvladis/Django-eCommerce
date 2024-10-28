from django.db import models

class AbstractCRMEvent(models.Model):

    body = models.TextField()

    TERMINAL, PARTNER, RECEIPT, DOC = "TERMINAL", "PARTNER", "RECEIPT", "DOC"
    INSTALLATION, STAFF, PRODUCT, MICS  = "INSTALLATION", "STAFF", "PRODUCT", "MICS"
    sender_choices = (
        (TERMINAL, "Терминал"),
        (PARTNER, "Точка продажи"),
        (RECEIPT, "Чек"),
        (DOC, "Документы"),
        (INSTALLATION, "Установка / Удаление"),
        (STAFF, "Персонал"),
        (PRODUCT, "Продукты"),
        (MICS, "Неизвестно"),
    )
    sender = models.CharField(max_length=32, choices=sender_choices, default=MICS)
    
    CREATION, DELETE, UPDATE, INFO = "CREATION", "DELETE", "UPDATE", "INFO"
    type_choices = (   
        (CREATION, "Создание"),
        (DELETE, "Удаление"),
        (UPDATE, "Обновление"),
        (INFO, "Инфо"),
    )
    type = models.CharField(max_length=255, choices=type_choices, default=INFO)

    date_created = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        abstract = True
        app_label = "crm"
        ordering = ("-date_created",)
        verbose_name = "Событие СRM"
        verbose_name_plural = "События СRM"

