import json
import datetime
from django.conf import settings
from rest_framework.renderers import JSONRenderer
from oscar.apps.checkout.signals import post_payment
from oscar.apps.order.serializers import OrderSerializer
from oscar.apps.order.signals import order_status_changed, active_order_placed
from .tasks import _send_site_notification_new_order_to_customer, _send_site_notification_new_order_to_staff, _send_site_notification_order_status_to_customer, _send_order_to_evotor, _send_push_notification_new_order_to_staff, _send_sms_notification_order_status_to_customer, _send_telegram_message_new_order_to_staff

def notify_about_new_order(sender, view, **kwargs):

    order = kwargs['order']
    order_str = create_order_list(order)
    order_time = format_order_time(order.order_time)
    
    ctx = {
        'user': order.user.get_name_and_phone(),
        'user_id': order.user.id,
        'source': order.sources.first().source_type.name,
        'shipping_method': order.shipping_method,
        'order_time': order_time,
        'number': order.number,
        'total': int(order.total),
        'order': order_str,
        'order_id': order.id,
        'url': order.get_full_url(),
        'staff_url': order.get_staff_url(),
    }

    if not settings.DEBUG: 
        _send_site_notification_new_order_to_customer.delay(ctx)
    else: 
        _send_site_notification_new_order_to_customer(ctx)

post_payment.connect(notify_about_new_order) 

def notify_customer_about_order_status(sender, order, **kwargs):
    ctx = {
        'user_id': order.user.id,
        'phone': order.user.username,
        'number': order.number,
        'new_status': kwargs['new_status'],
        'shipping_method': order.shipping_method,
        'url': order.get_absolute_url(),
        'order_id': order.id,
    }

    if not settings.DEBUG:
        _send_site_notification_order_status_to_customer.delay(ctx)
        _send_sms_notification_order_status_to_customer.delay(ctx)
    else:
        _send_site_notification_order_status_to_customer(ctx)
        _send_sms_notification_order_status_to_customer(ctx)
    
order_status_changed.connect(notify_customer_about_order_status)

def active_order_created(sender, order, **kwargs):
    serializer = OrderSerializer(order)
    order_json = json.loads(JSONRenderer().render(serializer.data).decode("utf-8"))

    order_str = create_order_list(order)
    order_time = format_order_time(order.order_time)
    
    ctx = {
        'user': order.user.get_name_and_phone(),
        'user_id': order.user.id,
        'source': order.sources.first().source_type.name,
        'shipping_method': order.shipping_method,
        'order_time': order_time,
        'number': order.number,
        'total': int(order.total),
        'order': order_str,
        'order_id': order.id,
        'url': order.get_full_url(),
        'staff_url': order.get_staff_url(),
    }

    if not settings.DEBUG: 
        _send_order_to_evotor.delay(order_json)
        _send_site_notification_new_order_to_staff.delay(ctx)
        _send_push_notification_new_order_to_staff.delay(ctx)
        _send_telegram_message_new_order_to_staff.delay(ctx)
    else: 
        _send_order_to_evotor(order_json)
        _send_site_notification_new_order_to_staff(ctx)
        _send_push_notification_new_order_to_staff(ctx)
        _send_telegram_message_new_order_to_staff(ctx)
    
active_order_placed.connect(active_order_created)

# helpers

def create_order_list(order):
    """Создает строку с перечнем товаров"""
    return ", ".join([f"{line.product.get_name()} ({line.quantity})" for line in order.lines.all()])

def format_order_time(order_time):
    """Форматирует время заказа"""
    if isinstance(order_time, datetime.date):
        return order_time.strftime('%d.%m.%Y %H:%M')
    return order_time