import logging
import os

from celery import Celery
from celery.signals import setup_logging
from decouple import config
# from celery.schedules import crontab 

CELERY_LOGGER_NAME = "celery"

@setup_logging.connect
def setup_celery_logging(loglevel=None, **kwargs):
    """Skip default Celery logging configuration.

    Will rely on Django to set up the base root logger.
    Celery loglevel will be set if provided as Celery command argument.
    """
    if loglevel:
        logging.getLogger(CELERY_LOGGER_NAME).setLevel(loglevel)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", config("DJANGO_SETTINGS_MODULE"))
app = Celery("Mikado")
app.config_from_object("django.conf:defaults", namespace="CELERY")
app.autodiscover_tasks()





