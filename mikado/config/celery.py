import logging
import os

from django.conf import settings
from celery import Celery
from celery.signals import setup_logging

from django.apps import apps 

CELERY_LOGGER_NAME = "celery"

@setup_logging.connect
def setup_celery_logging(loglevel=None, **kwargs):
    """Skip default Celery logging configuration.

    Will rely on Django to set up the base root logger.
    Celery loglevel will be set if provided as Celery command argument.
    """
    if loglevel:
        logging.getLogger(CELERY_LOGGER_NAME).setLevel(loglevel)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mikado.config.settings")
app = Celery("mikado-celery")
app.config_from_object(settings, namespace="CELERY")

# app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')