import os
import logging
from decouple import config

from django.conf import settings

from celery.signals import setup_logging
from celery import Celery

BROKER_URL = "redis://127.0.0.1:6379/10"
CELERY_LOGGER_NAME = "celery"


@setup_logging.connect
def setup_celery_logging(loglevel=None, **kwargs):
    """Skip default Celery logging configuration.

    Will rely on Django to set up the base root logger.
    Celery loglevel will be set if provided as Celery command argument.
    """
    if loglevel:
        logging.getLogger(CELERY_LOGGER_NAME).setLevel(loglevel)
    else:
        logging.getLogger(CELERY_LOGGER_NAME).setLevel(logging.DEBUG)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", config("DJANGO_SETTINGS_MODULE"))
app = Celery("celery", broker=BROKER_URL, backend=BROKER_URL)
app.config_from_object(settings, namespace="CELERY")

app.conf.broker_read_url = BROKER_URL
app.conf.broker_url = BROKER_URL
app.conf.broker_write_url = BROKER_URL
app.conf.result_backend = BROKER_URL
app.conf.timezone = "Asia/Krasnoyarsk"

app.autodiscover_tasks()
