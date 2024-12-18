from django.db import models
from django.urls import reverse

from oscar.apps.catalogue.reviews.utils import get_default_review_status
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
        related_name="reviews",
    )

    FOR_MODERATION, APPROVED, REJECTED = 0, 1, 2
    STATUS_CHOICES = (
        (FOR_MODERATION, "Не просмотрен"),
        (APPROVED, "Одобренный"),
        (REJECTED, "Отклоненный"),
    )

    status = models.SmallIntegerField(
        "Статус", choices=STATUS_CHOICES, default=get_default_review_status
    )

    date_created = models.DateTimeField(auto_now_add=True)

    is_open = models.BooleanField("Отзыв просмотрен", default=False, db_index=True)

    # Managers
    objects = ProductReviewQuerySet.as_manager()

    class Meta:
        app_label = "reviews"
        unique_together = (("product", "user"),)
        verbose_name ="Отзыв товара"
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
    def pending_moderation(self):
        return self.status == self.FOR_MODERATION

    @property
    def is_approved(self):
        return self.status == self.APPROVED

    @property
    def is_rejected(self):
        return self.status == self.REJECTED

    @property
    def reviewer_name(self):
        if self.user:
            name = self.user.get_full_name()

    # Helpers

    # def update_totals(self):
    #     """
    #     Update total and delta votes
    #     """
    #     result = self.votes.aggregate(score=Sum("delta"), total_votes=Count("id"))
    #     self.total_votes = result["total_votes"] or 0
    #     self.delta_votes = result["score"] or 0
    #     self.save()

    # def can_user_vote(self, user):
        # """
        # Test whether the passed user is allowed to vote on this
        # review
        # """
        # if not user.is_authenticated:
        #     return False, "Только авторизованные пользователи могут оставлять отзывы"
        # # pylint: disable=no-member
        # vote = self.votes.model(review=self, user=user, delta=1)
        # try:
        #     vote.full_clean()
        # except ValidationError as e:
        #     return False, "%s" % e
        # return True, ""


# class Vote(models.Model):
#     """
#     Records user ratings as yes/no vote.

#     * Only signed-in users can vote.
#     * Each user can vote only once.
#     """

#     review = models.ForeignKey(
#         "reviews.ProductReview", on_delete=models.CASCADE, related_name="votes"
#     )
#     user = models.ForeignKey(
#         AUTH_USER_MODEL, related_name="review_votes", on_delete=models.CASCADE
#     )
#     UP, DOWN = 1, -1
#     VOTE_CHOICES = ((UP, "Вверх"), (DOWN, "Вниз"))
#     delta = models.SmallIntegerField("Разница", choices=VOTE_CHOICES)
#     date_created = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         app_label = "reviews"
#         ordering = ["-date_created"]
#         unique_together = (("user", "review"),)
#         verbose_name = "Оценка"
#         verbose_name_plural = "Оценки"

#     def __str__(self):
#         return "%s vote for %s" % (self.delta, self.review)

#     def clean(self):
#         if not self.review.is_anonymous and self.review.user == self.user:
#             raise ValidationError("Вы не можете голосовать за свои отзывы")
#         if not self.user.id:
#             raise ValidationError("Голосовать за отзывы могут только авторизованные пользователи.")
#         previous_votes = self.review.votes.filter(user=self.user)
#         if len(previous_votes) > 0:
#             raise ValidationError("За отзыв можно проголосовать только один раз")

#     def save(self, *args, **kwargs):
#         super().save(*args, **kwargs)
#         self.review.update_totals()
