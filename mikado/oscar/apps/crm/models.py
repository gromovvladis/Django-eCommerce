from django.db import models

class CRMEvent(models.Model):

    body = models.TextField()

    TERMINAL, STORE, ORDER, DOC = "TERMINAL", "STORE", "ORDER", "DOC"
    INSTALLATION, STAFF, PRODUCT, GROUP, MICS  = "INSTALLATION", "STAFF", "PRODUCT", "GROUP", "MICS"
    sender_choices = (
        (TERMINAL, "Терминал"),
        (STORE, "Магазин"),
        (ORDER, "Заказ"),
        (DOC, "Документы"),
        (INSTALLATION, "Установка / Удаление"),
        (STAFF, "Персонал"),
        (PRODUCT, "Товар"),
        (GROUP, "Группа"),
        (MICS, "Неизвестно"),
    )
    sender = models.CharField(max_length=32, choices=sender_choices, default=MICS)
    
    CREATION, DELETE, UPDATE, INFO, BULK, ERROR = "CREATION", "DELETE", "UPDATE", "INFO", "BULK", "ERROR"
    type_choices = (   
        (CREATION, "Создание"),
        (DELETE, "Удаление"),
        (UPDATE, "Обновление"),
        (INFO, "Инфо"),
        (BULK, "Переодическая задача"),
        (ERROR, "Ошибка"),
    )
    event_type = models.CharField(max_length=255, choices=type_choices, default=INFO)

    date_created = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        app_label = "crm"
        ordering = ("-date_created",)
        verbose_name = "Событие Эвотор"
        verbose_name_plural = "События Эвотор"


class CRMBulk(models.Model):
    evotor_id = models.CharField(
        "ID Эвотор",
        max_length=128,
        blank=True,
        null=True,
    )
    PRODUCT, PRODUCT_GROUP = (
        "product",
        "product-group",
    )
    TYPE_CHOICES = (
        (PRODUCT, "Товары или доп. товары"),
        (PRODUCT_GROUP, "Категории"),
    )
    object_type = models.CharField(
        "Тип объектов", default=PRODUCT, choices=TYPE_CHOICES, max_length=128
    )
    ACCEPTED, RUNNING, COMPLETED, DECLINED, FAILED = (
        "ACCEPTED",
        "RUNNING",
        "COMPLETED",
        "DECLINED",
        "FAILED",
    )
    STATUS_CHOICES = (
        (ACCEPTED, "Задача принята в работу"),
        (RUNNING, "Задача обрабатывается"),
        (COMPLETED, "Обработка задачи завершена"),
        (DECLINED, "Задача отклонена"),
        (FAILED, "Обработать задачу не удалось"),
    )
    status = models.CharField(
        "Статус задачи", default=ACCEPTED, choices=STATUS_CHOICES, max_length=128
    )
    date_created = models.DateTimeField(
        "Дата создания", auto_now_add=True
    )
    date_finish = models.DateTimeField(
        "Дата окончания", blank=True, null=True
    )

    FINAL_STATUSES = (
        "COMPLETED",
        "DECLINED",
        "FAILED",
    )

    class Meta:
        app_label = "crm"
        ordering = ("-date_created",)
        verbose_name = "Массовая задача Эвотор"
        verbose_name_plural = "Массовая задача Эвотор"