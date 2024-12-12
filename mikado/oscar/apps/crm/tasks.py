from celery.exceptions import MaxRetriesExceededError
from celery import shared_task
import logging

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
            sender=CRMEvent.PRODUCT if bulk.object_type == bulk.PRODUCT else CRMEvent.GROUP,
            event_type=CRMEvent.BULK,
        )

        response = EvotorAPICloud().get_bulk_by_id(bulk_evotor_id)
        bulk = EvotorAPICloud().finish_bulk(bulk, response)

        if bulk.status not in CRMBulk.FINAL_STATUSES:
            interval = 5 if self.request.retries <= 3 else 30
            self.retry(countdown=interval)

    except MaxRetriesExceededError:
        logger.error(f"Задача превысила максимальное количество попыток для evotor_id={bulk_evotor_id}.")
    except Exception as exc:
        logger.error(f"Ошибка при выполнении задачи для evotor_id={bulk_evotor_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=30) 
        