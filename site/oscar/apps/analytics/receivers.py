from django.conf import settings
from django.dispatch import receiver
from django.db import transaction
from django.db.models import Sum

from oscar.apps.basket.signals import basket_addition
from oscar.apps.catalogue.signals import product_viewed
from oscar.apps.order.signals import order_placed
from oscar.apps.search.signals import user_search
from oscar.apps.analytics.tasks import (
    record_products_in_order_task,
    record_user_order_task,
    update_counter_task,
    user_searched_product_task,
    user_viewed_product_task,
)


# pylint: disable=unused-argument
@receiver(product_viewed)
def receive_product_view(sender, product, user, **kwargs):
    if kwargs.get("raw", False):
        return
    if settings.DEBUG:
        update_counter_task("ProductRecord", "num_views", {"product_id": product.id})
    else:
        update_counter_task.delay(
            "ProductRecord", "num_views", {"product_id": product.id}
        )

    if user and user.is_authenticated:
        if settings.DEBUG:
            update_counter_task("UserRecord", "num_product_views", {"user_id": user.id})
            user_viewed_product_task(product.id, user.id)
        else:
            update_counter_task.delay(
                "UserRecord", "num_product_views", {"user_id": user.id}
            )
            user_viewed_product_task.delay(product.id, user.id)


# pylint: disable=unused-argument
@receiver(user_search)
def receive_product_search(sender, query, user, **kwargs):
    if user and user.is_authenticated and not kwargs.get("raw", False):
        if settings.DEBUG:
            user_searched_product_task(user.id, query)
        else:
            user_searched_product_task.delay(user.id, query)


# pylint: disable=unused-argument
@receiver(basket_addition)
def receive_basket_addition(sender, product, user, **kwargs):
    if kwargs.get("raw", False):
        return
    if settings.DEBUG:
        update_counter_task(
            "ProductRecord", "num_basket_additions", {"product_id": product.id}
        )
    else:
        update_counter_task.delay(
            "ProductRecord", "num_basket_additions", {"product_id": product.id}
        )

    if user and user.is_authenticated:
        if settings.DEBUG:
            update_counter_task(
                "UserRecord", "num_basket_additions", {"user_id": user.id}
            )
        else:
            update_counter_task.delay(
                "UserRecord", "num_basket_additions", {"user_id": user.id}
            )


@receiver(order_placed)
def receive_order_placed(sender, order, user, **kwargs):
    if kwargs.get("raw", False):
        return

    def execute_tasks():
        order_data = {
            "total": order.total,
            "date_placed": order.date_placed,
            "num_lines": order.lines.count(),
            "lines": list(order.lines.values_list("product_id", "quantity")),
            "num_items": order.lines.aggregate(total_items=Sum("quantity"))[
                "total_items"
            ],
        }

        if settings.DEBUG:
            record_products_in_order_task(order_data)
        else:
            record_products_in_order_task.delay(order_data)

        if user and user.is_authenticated:
            if settings.DEBUG:
                record_user_order_task(user.id, order_data)
            else:
                record_user_order_task.delay(user.id, order_data)

    transaction.on_commit(execute_tasks)
