from django.db.models import Q


class StoreProductFilterMixin:
    def filter_queryset(self, queryset):
        """
        Restrict the queryset to products the given user has access to.
        A staff user is allowed to access all Products.
        A non-staff user is only allowed access to a product if they are in at
        least one stock record's store user list.
        """
        user = self.request.user
        if user.is_staff:
            return queryset

        return queryset.filter(
            Q(children__stockrecords__store__users__pk=user.pk)
            | Q(stockrecords__store__users__pk=user.pk)
        ).distinct()
