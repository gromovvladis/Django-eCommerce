from decimal import Decimal
from django.db import models
from oscar.core.compat import AUTH_USER_MODEL


class ProductRecord(models.Model):
    """
    A record of a how popular a product is.

    This used be auto-merchandising to display the most popular
    products.
    """

    product = models.OneToOneField(
        "catalogue.Product",
        verbose_name="Товар",
        related_name="stats",
        on_delete=models.CASCADE,
    )

    # Data used for generating a score
    num_views = models.PositiveIntegerField("Просмотры товара", default=0)
    num_basket_additions = models.PositiveIntegerField("Дополнения корзины", default=0)
    num_purchases = models.PositiveIntegerField("Покупки", default=0, db_index=True)

    # Product score - used within search
    score = models.FloatField("Счет", default=0.00)

    class Meta:
        app_label = "analytics"
        ordering = ["-num_purchases"]
        verbose_name = "Запись товара"
        verbose_name_plural = "Записи товаров"

    def __str__(self):
        return "Запись товара '%s'" % self.product


class UserRecord(models.Model):
    """
    A record of a user's activity.
    """

    user = models.OneToOneField(
        AUTH_USER_MODEL, verbose_name="Пользователь", on_delete=models.CASCADE
    )

    # Browsing stats
    num_product_views = models.PositiveIntegerField("Просмотры товара", default=0)
    num_basket_additions = models.PositiveIntegerField("Дополнения корзины", default=0)

    # Order stats
    num_orders = models.PositiveIntegerField(
        "Количество заказов", default=0, db_index=True
    )
    num_order_lines = models.PositiveIntegerField(
        "Количество позиций", default=0, db_index=True
    )
    num_order_items = models.PositiveIntegerField(
        "Количество товаров", default=0, db_index=True
    )
    total_spent = models.DecimalField(
        "Общая сумма покупок", decimal_places=2, max_digits=12, default=Decimal("0.00")
    )
    date_last_order = models.DateTimeField(
        "Дата последнего заказа", blank=True, null=True
    )

    class Meta:
        app_label = "analytics"
        verbose_name = "Запись пользователя"
        verbose_name_plural = "Записи пользователей"


class UserProductView(models.Model):
    user = models.ForeignKey(
        AUTH_USER_MODEL, verbose_name="Пользователь", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        "catalogue.Product", on_delete=models.CASCADE, verbose_name="Товар"
    )
    date_created = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        app_label = "analytics"
        ordering = ["-pk"]
        verbose_name = "Просмотр товара пользователем"
        verbose_name_plural = "Просмотры товара пользователями"

    def __str__(self):
        return "%(user)s посмотрел товар '%(product)s'" % {
            "user": self.user,
            "product": self.product,
        }


class UserSearch(models.Model):
    user = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    query = models.CharField("Поисковое условие", max_length=255, db_index=True)
    date_created = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        app_label = "analytics"
        ordering = ["-pk"]
        verbose_name = "Поисковый запрос пользователя"
        verbose_name_plural = "Поисковые запросы пользователей"

    def __str__(self):
        return "%(user)s искал '%(query)s'" % {
            "user": self.user,
            "query": self.query,
        }
