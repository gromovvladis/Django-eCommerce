import datetime
from django.conf import settings
from oscar.apps.checkout.signals import post_payment
from oscar.apps.order.signals import order_status_changed
from .tasks import _notify_admin_about_new_order, _notify_customer_about_new_order, _notify_customer_about_order_status, _send_telegram_message_to_users

def notify_about_new_order(sender, view, **kwargs):

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
        'shipping_method': kwargs['order'].shipping_method,
        'order_time': order_time,
        'number': kwargs['order'].number,
        'total': int(kwargs['order'].total),
        'order': order,
        'order_id': kwargs['order'].id,
        'url': kwargs['order'].get_full_url(),
    }

    msg = (
        f"<b>Новый заказ №{ctx['number']}</b>\n\n"
        f"{ctx['order']}\n\n"
        f"Время заказа: {ctx['order_time']}\n"
        f"Пользователь: {ctx['user']}\n"
        f"Оплата: {ctx['source']}\n"
        f"Доставка: {ctx['shipping_method']}\n"
        f"Сумма: {ctx['total']} ₽\n\n"
        f"<a href='{ctx['url']}'>Смотреть на сайте</a>"
    )
    
    if not settings.DEBUG: 
        _notify_admin_about_new_order.delay(ctx)
        _notify_customer_about_new_order.delay(ctx)
        _send_telegram_message_to_users.delay(msg, 'HTML')
    else: 
        _notify_admin_about_new_order(ctx)
        _notify_customer_about_new_order(ctx)
        _send_telegram_message_to_users(msg, 'HTML')

post_payment.connect(notify_about_new_order) 

def notify_customer_about_order_status(sender, order, **kwargs):
    ctx = {
        'user_id': order.user.id,
        'number': kwargs['order'].number,
        'new_status': kwargs['new_status'],
        'url': order.get_absolute_url(),
        'order_id': kwargs['order'].id,
    }

    if not settings.DEBUG:
        _notify_customer_about_order_status.delay(ctx)
    else:
        _notify_customer_about_order_status(ctx)
    
order_status_changed.connect(notify_customer_about_order_status)
