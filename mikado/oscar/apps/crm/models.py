from django.db import models

class CRMEvent(models.Model):

    body = models.TextField()

    TERMINAL, STORE, ORDER, DOC = "TERMINAL", "STORE", "ORDER", "DOC"
    INSTALLATION, STAFF, PRODUCT, MICS  = "INSTALLATION", "STAFF", "PRODUCT", "MICS"
    sender_choices = (
        (TERMINAL, "Терминал"),
        (STORE, "Магазин"),
        (ORDER, "Заказ"),
        (DOC, "Документы"),
        (INSTALLATION, "Установка / Удаление"),
        (STAFF, "Персонал"),
        (PRODUCT, "Товар"),
        (MICS, "Неизвестно"),
    )
    sender = models.CharField(max_length=32, choices=sender_choices, default=MICS)
    
    DELETE, UPDATE, INFO, ERROR ="DELETE", "UPDATE", "INFO", "ERROR"
    type_choices = (
        (DELETE, "Удаление"),
        (UPDATE, "Обновление"),
        (INFO, "Инфо"),
        (ERROR, "Ошибка"),
    )
    type = models.CharField(max_length=255, choices=type_choices, default=INFO)

    date_created = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        app_label = "crm"
        ordering = ("-date_created",)
        verbose_name = "Событие СRM"
        verbose_name_plural = "События СRM"
