import logging

from core.loading import get_class
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

AlertsDispatcher = get_class("webshop.customer.alerts.utils", "AlertsDispatcher")


class Command(BaseCommand):
    """
    Check stock records of products for availability and send out alerts
    to customers that have registered for an alert.
    """

    help = "Проверяйте наличие товаров, которые снова есть на складе, и отправляйте оповещения"

    def handle(self, *args, **options):
        """
        Check all products with active product alerts for
        availability and send out email alerts when a product is
        available to buy.
        """
        AlertsDispatcher().send_alerts()
