import datetime
from django.conf import settings
from oscar.apps.checkout.signals import post_payment
from oscar.apps.order.signals import order_status_changed
from .tasks import _notify_staff_about_new_order, _notify_customer_about_new_order, _notify_customer_about_order_status, _send_telegram_message_new_order_to_staff

def notify_about_new_order(sender, view, **kwargs):

    order_list = []

    for line in kwargs['order'].basket.lines.all():
            order_list.append("%s (%s)" % (line.product.get_name(), line.quantity))
    
    order = ", ".join(order_list)
    
    order_time = kwargs['order'].order_time

    if order_time is datetime.date:
        order_time = order_time.strftime('%d.%m.%Y %H:%M')

    ctx = {
        'user': kwargs['order'].user.get_name_and_phone(),
        'user_id': kwargs['order'].user.id,
        'source': kwargs['order'].sources.first().source_type.name,
        'shipping_method': kwargs['order'].shipping_method,
        'order_time': order_time,
        'number': kwargs['order'].number,
        'total': int(kwargs['order'].total),
        'order': order,
        'order_id': kwargs['order'].id,
        'url': kwargs['order'].get_full_url(),
        'staff_url': kwargs['order'].get_staff_url(),
    }
    
    if not settings.DEBUG: 
        _notify_customer_about_new_order.delay(ctx)
        _notify_staff_about_new_order.delay(ctx)
        _send_telegram_message_new_order_to_staff.delay(ctx)
    else: 
        _notify_staff_about_new_order(ctx)
        _notify_customer_about_new_order(ctx)
        _send_telegram_message_new_order_to_staff(ctx)

post_payment.connect(notify_about_new_order) 

def notify_customer_about_order_status(sender, order, **kwargs):
    ctx = {
        'user_id': order.user.id,
        'number': order.number,
        'new_status': kwargs['new_status'],
        'url': order.get_absolute_url(),
        'order_id': order.id,
    }

    if not settings.DEBUG:
        _notify_customer_about_order_status.delay(ctx)
    else:
        _notify_customer_about_order_status(ctx)
    
order_status_changed.connect(notify_customer_about_order_status)
