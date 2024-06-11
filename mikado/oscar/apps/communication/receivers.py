from django.template import loader
from oscar.apps.checkout.signals import post_payment
from oscar.apps.order.signals import order_status_changed
from oscar.core.loading import get_model
from django.contrib.auth import get_user_model
from celery import shared_task

Notification = get_model("communication", "Notification")
User = get_user_model()

admins = User.objects.filter(is_staff=True)


def notify_admin_about_new_order(sender, view, **kwargs):
    ctx = {
        'order': kwargs['order']
    }
    _notify_admin_about_new_order.delay(ctx)

post_payment.connect(notify_admin_about_new_order)

@shared_task
def _notify_admin_about_new_order(ctx, **kwargs):

    subject = "Новый заказ"
    message_tpl = loader.get_template("oscar/customer/alerts/new_order_message.html")
    description = "Заказ №%s успешно создан!" % (ctx['order'].number)

    context = {
        'order': ctx['order'],
        'description': description
    }

    for user in admins:
        Notification.objects.create(
            recipient=user, 
            subject=subject, 
            body=message_tpl.render(context).strip(), 
            description=description,
            status="Success"
        )



def notify_user_about_new_order(sender, view, order, **kwargs):

    ctx = {
        'order': order,
    }

    _notify_user_about_new_order.delay(ctx)

post_payment.connect(notify_user_about_new_order)

@shared_task
def _notify_user_about_new_order(ctx, **kwargs):
    
    subject = "Пользовательский заказ"
    message_tpl = loader.get_template("oscar/customer/alerts/staff_new_order_message.html")
    description = "Заказ №%s успешно создан!" % (ctx['order'].number)

    context = {
        'order': ctx['order'],
        'description': description
    }

    Notification.objects.create(
        recipient=ctx['order'].user,
        subject=subject,
        body=message_tpl.render(context).strip(), 
        description=description,
        status="Success"
    )

    

def notify_user_about_order_status(sender, order, **kwargs):
    
    ctx = {
        'order': order,
        'new_status': kwargs['new_status'],
    }

    _notify_user_about_order_status.delay(ctx)
    
order_status_changed.connect(notify_user_about_order_status)

@shared_task
def _notify_user_about_order_status(ctx, **kwargs):
    
    subject = "Статус заказа изменен"
    message_tpl = loader.get_template("oscar/customer/alerts/order_status_chenged_message.html")
    description = "Новый статус заказа №%s - %s" % (ctx['order'].number, kwargs['new_status'])

    status="Info"

    if ctx['order'].status == "Отменен":
        status="Canceled"

    if ctx['order'].status == "Обрабатывается" or ctx['order'].status == "Ожидает оплаты":
        status="Warning"


    context = {
        'order': ctx['order'],
        'new_status': kwargs['new_status'],
        'description': description
    }

    Notification.objects.create(
        recipient=ctx['order'].user,
        subject=subject,
        body=message_tpl.render(context).strip(),
        description=description,
        status=status,
    )
    