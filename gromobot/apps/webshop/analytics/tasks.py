import logging

from celery import shared_task
from core.compat import get_user_model
from core.loading import get_model
from django.apps import apps
from django.conf import settings
from django.db.models import F

ProductRecord = get_model("analytics", "ProductRecord")
UserProductView = get_model("analytics", "UserProductView")
UserRecord = get_model("analytics", "UserRecord")
UserSearch = get_model("analytics", "UserSearch")
Order = get_model("order", "Order")
Product = get_model("catalogue", "Product")
User = get_user_model()

logger = logging.getLogger("apps.webshop.analytics")


@shared_task
def update_counter_task(model_name, field_name, filter_kwargs, increment=1):
    """
    Обновляет счетчик в модели. Если записи нет — создает новую.

    Efficiently updates a counter field by a given increment. Uses Django's
    update() call to fetch and update in one query.

    TODO: This has a race condition, we should use UPSERT here

    :param model: The model class of the recording model
    :param field_name: The name of the field to update
    :param filter_kwargs: Parameters to the ORM's filter() function to get the
    correct instance
    """
    try:
        model = apps.get_model("analytics", model_name)
        record = model.objects.filter(**filter_kwargs)
        affected = record.update(**{field_name: F(field_name) + increment})
        if not affected:
            filter_kwargs[field_name] = increment
            model.objects.create(**filter_kwargs)
    except Exception as e:
        logger.error(f"{e} update_counter_task при обновлении {model_name}")


@shared_task
def record_products_in_order_task(order_data):
    """
    Записывает данные о товарах в заказе.
    """
    try:
        updates = [
            update_counter_task.s(
                "ProductRecord",
                "num_purchases",
                {"product_id": product_id},
                line_quantity,
            )
            for product_id, line_quantity in order_data["lines"]
        ]
        for task in updates:
            if settings.CELERY:
                task.delay()
            else:
                task()
    except Exception as e:
        logger.error(
            f"{e} при записи продуктов в заказе пользователя (date_placed={order_data['date_placed']})"
        )


@shared_task
def record_user_order_task(user_id, order_data):
    """
    Записывает данные о заказе пользователя.
    """
    try:
        record = UserRecord.objects.filter(user_id=user_id)
        affected = record.update(
            num_orders=F("num_orders") + 1,
            num_order_lines=F("num_order_lines") + order_data["num_lines"],
            num_order_items=F("num_order_items") + order_data["num_items"],
            total_spent=F("total_spent") + order_data["total"],
            date_last_order=order_data["date_placed"],
        )
        if not affected:
            UserRecord.objects.create(
                user_id=user_id,
                num_orders=1,
                num_order_lines=order_data["num_lines"],
                num_order_items=order_data["num_items"],
                total_spent=order_data["total"],
                date_last_order=order_data["date_placed"],
            )
    except Exception as e:
        logger.error(f"{e} при записи заказа пользователя (user_id={user_id})")


@shared_task
def user_viewed_product_task(product_id, user_id):
    """
    Записывает факт просмотра товара пользователем.
    """
    try:
        UserProductView.objects.create(product_id=product_id, user_id=user_id)
    except Exception as e:
        logger.error(
            f"Ошибка user_viewed_product_task при записи заказа пользователя {e}"
        )


@shared_task
def user_searched_product_task(user_id, query):
    """
    Записывает факт поиска пользователем.
    """
    try:
        UserSearch.objects.create(user_id=user_id, query=query)
    except Exception as e:
        logger.error(
            f"Ошибка user_searched_product_task при записи заказа пользователя {e}"
        )
