import datetime
from django.conf import settings
from oscar.apps.checkout.signals import post_payment
from oscar.apps.order.signals import order_status_changed
from .tasks import _notify_admin_about_new_order, _notify_user_about_new_order, _notify_user_about_order_status


def notify_admin_about_new_order(sender, view, **kwargs):

    if not settings.DEBUG: 
        
        order_list = []

        for line in kwargs['order'].basket.lines.all():
                order_list.append("%s (%s)" % (line.product.get_title(), line.quantity))
        
        order = ", ".join(order_list)

        order_time = kwargs['order'].order_time
        
        if order_time is datetime.date:
            order_time = order_time.strftime('%d.%m.%Y %H:%M')

        ctx = {
            'user': kwargs['order'].user.get_name_and_phone(),
            'user_id': kwargs['order'].user.id,
            'source': kwargs['order'].sources.first().source_type.name,
            'status': kwargs['order'].status,
            'shipping_method': kwargs['order'].shipping_method,
            'order_time': order_time,
            'number': kwargs['order'].number,
            'total': int(kwargs['order'].total),
            'order': order,
            'order_id': kwargs['order'].id,
        }

        _notify_admin_about_new_order.delay(ctx)
        _notify_user_about_new_order.delay(ctx)

post_payment.connect(notify_admin_about_new_order) 


def notify_user_about_order_status(sender, order, **kwargs):
    
    if not settings.DEBUG:
        ctx = {
            'user_id': order.user.id,
            'title': order.title,
            'new_status': kwargs['new_status'],
            'url': order.get_absolute_url(),
            'order_id': kwargs['order'].id,
        }
        _notify_user_about_order_status.delay(ctx)
    
order_status_changed.connect(notify_user_about_order_status)
