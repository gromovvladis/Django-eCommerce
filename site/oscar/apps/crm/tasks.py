import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from django.core.cache import cache

from oscar.apps.crm.client import EvatorCloud
from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")
Additional = get_model("catalogue", "Additional")
Category = get_model("catalogue", "Category")

logger = logging.getLogger("oscar.crm")


@shared_task(bind=True, max_retries=10)
def process_bulk_task(self, bulk_evotor_id):
    """
    Задача обработки bulks с ограничением на 10 попыток.
    """

    from .models import CRMEvent, CRMBulk
    from .client import EvotorAPICloud

    try:
        bulk = CRMBulk.objects.filter(evotor_id=bulk_evotor_id).first()
        if not bulk:
            logger.error(f"Bulk с evotor_id={bulk_evotor_id} не найден.")
            return

        CRMEvent.objects.create(
            sender=(
                CRMEvent.PRODUCT if bulk.object_type == bulk.PRODUCT else CRMEvent.GROUP
            ),
            event_type=CRMEvent.BULK,
        )

        response = EvotorAPICloud().get_bulk_by_id(bulk_evotor_id)
        bulk = EvotorAPICloud().finish_bulk(bulk, response)

        logger.info(f"Статус bulk {bulk.status}, попытки {self.request.retries}")

        if (
            bulk.status not in CRMBulk.FINAL_STATUSES
            and self.request.retries < self.max_retries
        ):
            interval = 5 if self.request.retries <= 3 else 30

            logger.info(f"Повторяем {bulk.status}")

            self.retry(countdown=interval)

    except MaxRetriesExceededError:
        logger.error(
            f"Задача превысила максимальное количество попыток для evotor_id={bulk_evotor_id}."
        )
    except Exception as exc:
        logger.error(
            f"Ошибка при выполнении задачи для evotor_id={bulk_evotor_id}: {exc}",
            exc_info=True,
        )
        raise self.retry(exc=exc, countdown=30)


# ====


@shared_task
def send_evotor_category_task(category_id):
    try:
        return EvatorCloud().update_or_create_evotor_category_by_id(category_id)
    except Exception as e:
        logger.error(
            "Ошибка при отправке созданной / измененной категории в Эвотор. Ошибка %s",
            e,
        )


@shared_task
def send_evotor_product_task(product_id):
    try:
        return EvatorCloud().update_or_create_evotor_product_by_id(product_id)
    except Exception as e:
        logger.error(
            "Ошибка при отправке созданной / измененной категории в Эвотор. Ошибка %s",
            e,
        )


@shared_task
def send_evotor_additional_task(additional_id):
    try:
        return EvatorCloud().update_or_create_evotor_additional_by_id(additional_id)
    except Exception as e:
        logger.error(
            "Ошибка при отправке созданной / измененной категории в Эвотор. Ошибка %s",
            e,
        )


@shared_task
def update_evotor_stockrecord_task(product_id):
    try:
        return EvatorCloud().update_evotor_stockrecord_by_id(product_id)
    except Exception as e:
        logger.error(
            "Ошибка при отправке измененной товароной записи товара в Эвотор. Ошибка %s",
            e,
        )


@shared_task
def delete_evotor_category_task(category_id):
    try:
        return EvatorCloud().delete_evotor_category_by_id(category_id)

    except Exception as e:
        logger.error(
            "Ошибка при отправке измененной товароной записи товара в Эвотор. Ошибка %s",
            e,
        )


@shared_task
def delete_evotor_product_task(product_id, store_id=None):
    try:
        if store_id is not None:
            return EvatorCloud().delete_evotor_product_by_store_by_id(
                product_id, store_id
            )

        return EvatorCloud().delete_evotor_product_by_id(product_id)
    except Exception as e:
        logger.error(
            "Ошибка при отправке измененной товароной записи товара в Эвотор. Ошибка %s",
            e,
        )


@shared_task
def delete_evotor_additional_task(additional_id):
    try:
        return EvatorCloud().delete_evotor_additional_by_id(additional_id)

    except Exception as e:
        logger.error(
            "Ошибка при отправке измененной товароной записи товара в Эвотор. Ошибка %s",
            e,
        )


# ====


@shared_task
def update_site_stores_task(data_items, is_filtered, user_id):
    try:
        msg, success = EvatorCloud().create_or_update_site_stores(
            data_items, is_filtered
        )
        cache_key = f"user_message_{user_id}"
        cache.set(cache_key, msg, timeout=3600)
    except Exception as e:
        logger.error(
            "Ошибка при отправке измененной товароной записи товара в Эвотор. Ошибка %s",
            e,
        )


@shared_task
def update_site_terminals_task(data_items, is_filtered, user_id):
    try:
        msg, success = EvatorCloud().create_or_update_site_terminals(
            data_items, is_filtered
        )
        cache_key = f"user_message_{user_id}"
        cache.set(cache_key, msg, timeout=3600)
    except Exception as e:
        logger.error(
            "Ошибка при отправке измененной товароной записи товара в Эвотор. Ошибка %s",
            e,
        )


@shared_task
def update_site_staffs_task(data_items, is_filtered, user_id):
    try:
        msg, success = EvatorCloud().create_or_update_site_staffs(
            data_items, is_filtered
        )
        cache_key = f"user_message_{user_id}"
        cache.set(cache_key, msg, timeout=3600)
    except Exception as e:
        logger.error(
            "Ошибка при отправке измененной товароной записи товара в Эвотор. Ошибка %s",
            e,
        )


@shared_task
def update_site_groups_task(data_items, is_filtered, user_id):
    try:
        msg, success = EvatorCloud().create_or_update_site_groups(
            data_items, is_filtered
        )
        cache_key = f"user_message_{user_id}"
        cache.set(cache_key, msg, timeout=3600)
    except Exception as e:
        logger.error(
            "Ошибка при отправке измененной товароной записи товара в Эвотор. Ошибка %s",
            e,
        )


@shared_task
def update_site_products_task(data_items, is_filtered, user_id):
    try:
        msg, success = EvatorCloud().create_or_update_site_products(
            data_items, is_filtered
        )
        cache_key = f"user_message_{user_id}"
        cache.set(cache_key, msg, timeout=3600)
    except Exception as e:
        logger.error(
            "Ошибка при отправке измененной товароной записи товара в Эвотор. Ошибка %s",
            e,
        )


@shared_task
def update_site_additionals_task(data_items, is_filtered, user_id):
    try:
        msg, success = EvatorCloud().create_or_update_site_additionals(
            data_items, is_filtered
        )
        cache_key = f"user_message_{user_id}"
        cache.set(cache_key, msg, timeout=3600)
    except Exception as e:
        logger.error(
            "Ошибка при отправке измененной товароной записи товара в Эвотор. Ошибка %s",
            e,
        )


# ====


@shared_task
def send_evotor_categories_task(category_ids, user_id):
    try:
        categories = Category.objects.filter(id__in=category_ids)
        error = EvatorCloud().update_or_create_evotor_groups(categories)

        if error:
            msg = error
        else:
            msg = "Категории были успешно отправлены в Эвотор!"

        cache_key = f"user_message_{user_id}"
        cache.set(cache_key, msg, timeout=3600)

    except Exception as e:
        logger.error(
            "Ошибка при отправке созданной / измененной категории или модификации в Эвотор. Ошибка %s",
            e,
        )


@shared_task
def send_evotor_products_task(product_ids, user_id):
    try:
        products = Product.objects.filter(id__in=product_ids)
        error = EvatorCloud().update_or_create_evotor_products(products)

        if error:
            msg = error
        else:
            msg = "Товары были успешно отправлены в Эвотор!"

        cache_key = f"user_message_{user_id}"
        cache.set(cache_key, msg, timeout=3600)

    except Exception as e:
        logger.error(
            "Ошибка при отправке созданной / измененной категории или модификации в Эвотор. Ошибка %s",
            e,
        )


@shared_task
def send_evotor_additionals_task(additional_ids, user_id):
    try:
        additionals = Additional.objects.filter(id__in=additional_ids)
        error = EvatorCloud().update_or_create_evotor_additionals(additionals)

        if error:
            msg = error
        else:
            msg = "Дополнительные товары были успешно отправлены в Эвотор!"

        cache_key = f"user_message_{user_id}"
        cache.set(cache_key, msg, timeout=3600)

    except Exception as e:
        logger.error(
            "Ошибка при отправке созданной / измененной категории или модификации в Эвотор. Ошибка %s",
            e,
        )
