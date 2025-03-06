from django.db import models
from django.urls import reverse

from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.loading import get_class

ProductReviewQuerySet = get_class("catalogue.reviews.managers", "ProductReviewQuerySet")


class ProductReview(models.Model):
    """
    A review of a product
    """

    product = models.ForeignKey(
        "catalogue.Product", related_name="reviews", null=True, on_delete=models.CASCADE
    )

    # Scores are between 0 and 5
    SCORE_CHOICES = tuple([(x, x) for x in range(0, 6)])
    score = models.SmallIntegerField("Оценка", choices=SCORE_CHOICES)

    body = models.TextField("Текст отзыва")

    # User information.
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="product_reviews",
    )

    UNKNOWN, HELPFUL, UNHELPFUL = 0, 1, 2
    STATUS_CHOICES = (
        (UNKNOWN, "Неизвестно"),
        (HELPFUL, "Полезный"),
        (UNHELPFUL, "Неполезный"),
    )

    status = models.SmallIntegerField("Статус", choices=STATUS_CHOICES, default=UNKNOWN)

    date_created = models.DateTimeField(auto_now_add=True)

    is_open = models.BooleanField("Отзыв просмотрен", default=False, db_index=True)

    # Managers
    objects = ProductReviewQuerySet.as_manager()

    class Meta:
        app_label = "reviews"
        unique_together = (("product", "user"),)
        verbose_name = "Отзыв товара"
        verbose_name_plural = "Отзывы товаров"

    def get_absolute_url(self):
        kwargs = {
            "product_slug": self.product.slug,
            "product_pk": self.product.id,
            "pk": self.id,
        }
        return reverse("catalogue:reviews-detail", kwargs=kwargs)

    def __str__(self):
        return self.product.name

    def clean(self):
        self.body = self.body.strip()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_rating()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if self.product is not None:
            self.product.update_rating()

    # Properties

    @property
    def is_anonymous(self):
        return self.user is None

    @property
    def pending(self):
        return self.status == self.UNKNOWN

    @property
    def is_helpful(self):
        return self.status == self.HELPFUL

    @property
    def is_unhelpful(self):
        return self.status == self.UNHELPFUL

    @property
    def reviewer_name(self):
        if self.user:
            return self.user.get_full_name()
