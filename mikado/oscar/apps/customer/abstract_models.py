from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

from oscar.apps.catalogue.reviews.utils import get_default_review_status
from oscar.core import validators

from oscar.core.compat import AUTH_USER_MODEL


class AbstractOrderReview(models.Model):
    """
    A review of a order
    """

    order = models.ForeignKey(
        "order.Order", related_name="reviews", null=True, on_delete=models.CASCADE
    )

    # Scores are between 0 and 5
    SCORE_CHOICES = tuple([(x, x) for x in range(5, 0, -1)])
    score = models.SmallIntegerField("Оценка", choices=SCORE_CHOICES)

    body = models.TextField("Текст отзыва")

    # User information.
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    # homepage = models.URLField("URL", blank=True)

    date_created = models.DateTimeField(auto_now_add=True)

    is_open = models.BooleanField("Отзыв просмотрен", default=False, db_index=True)

    class Meta:
        abstract = True
        db_table = "order_review"
        app_label = "customer"
        unique_together = (("order", "user"),)
        verbose_name ="Отзыв заказа"
        verbose_name_plural = "Отзывы заказов"

    def get_absolute_url(self):
        kwargs = {
            "order_slug": self.order.slug,
            "order_pk": self.order.id,
            "pk": self.id,
        }
        return reverse("customer:feedbacks", kwargs=kwargs)

    def __str__(self):
        return self.body

    def clean(self):
        self.body = self.body.strip()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    @property
    def reviewer_name(self):
        if self.user:
            return self.user.get_full_name()