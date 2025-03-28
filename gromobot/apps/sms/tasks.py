from celery import shared_task

from .services.clean import CleanService


@shared_task
def clear_expired():
    CleanService.clear()
