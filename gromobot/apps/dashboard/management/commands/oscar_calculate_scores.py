import logging

from core.loading import get_class
from django.core.management.base import BaseCommand

Calculator = get_class("webshop.analytics.scores", "Calculator")

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Calculate product scores based on analytics data"

    def handle(self, *args, **options):
        Calculator(logger).run()
