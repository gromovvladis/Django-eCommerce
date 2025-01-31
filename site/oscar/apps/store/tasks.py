import logging
from celery import shared_task

from django.core.cache import cache

logger = logging.getLogger("oscar.order")

# @shared_task
# def update_cache_product_task(product_id, store_id, *args, **kwargs):
#     cache.delete(f'product_compact_price_{product_id}_{store_id}')
#     cache.delete(f'product_detail_price_{product_id}_{store_id}')