from django.dispatch import receiver
from django.conf import settings

from oscar.apps.crm.tasks import (
    send_evotor_category_task,
    send_evotor_categories_task,
    send_evotor_product_task,
    send_evotor_products_task,
    send_evotor_additional_task,
    send_evotor_additionals_task,
    update_evotor_stockrecord_task,
    delete_evotor_category_task,
    delete_evotor_product_task,
    delete_evotor_additional_task,
    update_site_stores_task,
    update_site_terminals_task,
    update_site_staffs_task,
    update_site_groups_task,
    update_site_products_task,
    update_site_additionals_task,
)
from oscar.apps.crm.signals import (
    send_evotor_category,
    send_evotor_product,
    send_evotor_additional,
    send_evotor_categories,
    send_evotor_products,
    send_evotor_additionals,
    update_evotor_stockrecord,
    delete_evotor_category,
    delete_evotor_product,
    delete_evotor_additional,
    update_site_stores,
    update_site_terminals,
    update_site_staffs,
    update_site_groups,
    update_site_products,
    update_site_additionals,
)


@receiver(send_evotor_category)
def send_evotor_category_receiver(sender, category_id, user_id, **kwargs):
    if settings.CELERY:
        send_evotor_category_task.delay(category_id, user_id)
    else:
        send_evotor_category_task(category_id, user_id)


@receiver(send_evotor_product)
def send_evotor_product_receiver(sender, product_id, user_id, **kwargs):
    if settings.CELERY:
        send_evotor_product_task.delay(product_id, user_id)
    else:
        send_evotor_product_task(product_id, user_id)


@receiver(send_evotor_additional)
def send_evotor_additional_receiver(sender, additional_id, user_id, **kwargs):
    if settings.CELERY:
        send_evotor_additional_task.delay(additional_id, user_id)
    else:
        send_evotor_additional_task(additional_id, user_id)


@receiver(update_evotor_stockrecord)
def update_evotor_stockrecord(sender, product_id, user_id, **kwargs):
    if settings.CELERY:
        update_evotor_stockrecord_task.delay(product_id, user_id)
    else:
        update_evotor_stockrecord_task(product_id, user_id)


@receiver(delete_evotor_category)
def delete_evotor_category(sender, category_id, user_id, **kwargs):
    if settings.CELERY:
        delete_evotor_category_task.delay(category_id, user_id)
    else:
        delete_evotor_category_task(category_id, user_id)


@receiver(delete_evotor_product)
def delete_evotor_product(sender, product_id, user_id, store_id=None, **kwargs):
    if settings.CELERY:
        delete_evotor_product_task.delay(product_id, user_id, store_id)
    else:
        delete_evotor_product_task(product_id, user_id, store_id)


@receiver(delete_evotor_additional)
def delete_evotor_additional(sender, additional_id, user_id, **kwargs):
    if settings.CELERY:
        delete_evotor_additional_task.delay(additional_id, user_id)
    else:
        delete_evotor_additional_task(additional_id, user_id)


@receiver(update_site_stores)
def update_site_stores_receiver(sender, data_items, is_filtered, user_id, **kwargs):
    if settings.CELERY:
        update_site_stores_task.delay(data_items, is_filtered, user_id)
    else:
        update_site_stores_task(data_items, is_filtered, user_id)


@receiver(update_site_terminals)
def update_site_terminals_receiver(sender, data_items, is_filtered, user_id, **kwargs):
    if settings.CELERY:
        update_site_terminals_task.delay(data_items, is_filtered, user_id)
    else:
        update_site_terminals_task(data_items, is_filtered, user_id)


@receiver(update_site_staffs)
def update_site_staffs_receiver(sender, data_items, is_filtered, user_id, **kwargs):
    if settings.CELERY:
        update_site_staffs_task.delay(data_items, is_filtered, user_id)
    else:
        update_site_staffs_task(data_items, is_filtered, user_id)


@receiver(update_site_groups)
def update_site_groups_receiver(sender, data_items, is_filtered, user_id, **kwargs):
    if settings.CELERY:
        update_site_groups_task.delay(data_items, is_filtered, user_id)
    else:
        update_site_groups_task(data_items, is_filtered, user_id)


@receiver(update_site_products)
def update_site_products_receiver(sender, data_items, is_filtered, user_id, **kwargs):
    if settings.CELERY:
        update_site_products_task.delay(data_items, is_filtered, user_id)
    else:
        update_site_products_task(data_items, is_filtered, user_id)


@receiver(update_site_additionals)
def update_site_additionals_receiver(
    sender, data_items, is_filtered, user_id, **kwargs
):
    if settings.CELERY:
        update_site_additionals_task.delay(data_items, is_filtered, user_id)
    else:
        update_site_additionals_task(data_items, is_filtered, user_id)


@receiver(send_evotor_categories)
def send_evotor_categories_receiver(sender, category_ids, user_id, **kwargs):
    if settings.CELERY:
        send_evotor_categories_task.delay(category_ids, user_id)
    else:
        send_evotor_categories_task(category_ids, user_id)


@receiver(send_evotor_products)
def send_evotor_products_receiver(sender, product_ids, user_id, **kwargs):
    if settings.CELERY:
        send_evotor_products_task.delay(product_ids, user_id)
    else:
        send_evotor_products_task(product_ids, user_id)


@receiver(send_evotor_additionals)
def send_evotor_additionals_receiver(sender, additional_ids, user_id, **kwargs):
    if settings.CELERY:
        send_evotor_additionals_task.delay(additional_ids, user_id)
    else:
        send_evotor_additionals_task(additional_ids, user_id)
