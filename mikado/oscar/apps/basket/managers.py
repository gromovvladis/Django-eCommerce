from django.db import models


class OpenBasketManager(models.Manager):
    """For searching/creating OPEN baskets only."""

    status_filter = "Open"

    def get_queryset(self):
        return super().get_queryset().filter(status=self.status_filter)
    
    def get_or_create(self, **kwargs):
        return self.get_queryset().get_or_create(status=self.status_filter, **kwargs)

    # def get_or_create(self, **kwargs):
    #     """
    #     Gets or creates an open basket for the given owner.
    #     This method optimizes queries for related fields.
    #     """
    #     try:
    #         basket = self.get_queryset().select_related('owner').get(owner=kwargs['owner'])  # Добавьте сюда нужные поля
    #     except self.model.DoesNotExist:
    #         basket = self.model.objects.create(status=self.status_filter, owner=kwargs['owner'])
    #     return basket



# class SavedBasketManager(models.Manager):
#     """For searching/creating SAVED baskets only."""

#     status_filter = "Saved"

#     def get_queryset(self):
#         return super().get_queryset().filter(status=self.status_filter)

#     def create(self, **kwargs):
#         return self.get_queryset().create(status=self.status_filter, **kwargs)

#     def get_or_create(self, **kwargs):
#         return self.get_queryset().get_or_create(status=self.status_filter, **kwargs)
