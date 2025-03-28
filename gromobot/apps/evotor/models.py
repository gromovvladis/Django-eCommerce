from django.contrib.auth.models import Group
from django.db import models


class EvotorEvent(models.Model):
    body = models.TextField()
    INSTALLATION, STORE, TERMINAL, STAFF, GROUP, PRODUCT, ORDER, DOC, MICS = (
        "INSTALLATION",
        "STORE",
        "TERMINAL",
        "STAFF",
        "GROUP",
        "PRODUCT",
        "ORDER",
        "DOC",
        "MICS",
    )
    sender_choices = (
        (INSTALLATION, "Установка / Удаление"),
        (STORE, "Магазин"),
        (TERMINAL, "Терминал"),
        (STAFF, "Персонал"),
        (GROUP, "Группа"),
        (PRODUCT, "Товар"),
        (ORDER, "Заказ"),
        (DOC, "Документы"),
        (MICS, "Неизвестно"),
    )
    sender = models.CharField(max_length=32, choices=sender_choices, default=MICS)

    CREATION, DELETE, UPDATE, INFO, BULK, ERROR = (
        "CREATION",
        "DELETE",
        "UPDATE",
        "INFO",
        "BULK",
        "ERROR",
    )
    type_choices = (
        (CREATION, "Создание"),
        (DELETE, "Удаление"),
        (UPDATE, "Обновление"),
        (INFO, "Инфо"),
        (BULK, "Переодическая задача"),
        (ERROR, "Ошибка"),
    )
    event_type = models.CharField(max_length=32, choices=type_choices, default=INFO)

    date_created = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        ordering = ("-date_created",)
        verbose_name = "Событие Эвотор"
        verbose_name_plural = "События Эвотор"

    def __str__(self):
        return f"{self.event_type} - {self.body}"


class EvotorBulk(models.Model):
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
    date_created = models.DateTimeField("Дата создания", auto_now_add=True)
    date_finish = models.DateTimeField("Дата окончания", blank=True, null=True)

    FINAL_STATUSES = (
        "COMPLETED",
        "DECLINED",
        "FAILED",
    )

    class Meta:
        ordering = ("-date_created",)
        verbose_name = "Массовая задача Эвотор"
        verbose_name_plural = "Массовая задача Эвотор"

    def __str__(self):
        return f"{self.object_type} - {self.status} - {self.date_finish}"


class EvotorUserGroup(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="evotor")
    evotor_id = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.group.name

    class Meta:
        unique_together = (("group", "evotor_id"),)
        verbose_name = "Группа пользователей Эвотор"
        verbose_name_plural = "Группа пользователей Эвотор"


class EvotorUser(models.Model):
    pass


class EvotorSubscription(models.Model):
    pass
