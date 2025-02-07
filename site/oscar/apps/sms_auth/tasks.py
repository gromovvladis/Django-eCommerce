from .services.clean import CleanService
from celery import shared_task


@shared_task
def clear_expired():
    CleanService.clear()
