from django.template import loader
from celery import shared_task
from oscar.core.loading import get_model
from django.contrib.auth import get_user_model

Notification = get_model("communication", "Notification")
User = get_user_model()
admins = User.objects.filter(is_staff=True)

@shared_task
def _notify_admin_about_new_order(ctx: dict):

    subject = "Пользовательский заказ"
    message_tpl = loader.get_template("oscar/customer/alerts/staff_new_order_message.html")
    description = "Заказ №%s успешно создан!" % (ctx['number'])

    for user in admins:
        Notification.objects.create(
            recipient=user, 
            order_id=ctx["order_id"],
            subject=subject, 
            body=message_tpl.render(ctx).strip(), 
            description=description,
            status="Success"
        )

@shared_task()
def _notify_user_about_new_order(ctx: dict):
    
    subject = "Новый заказ"
    message_tpl = loader.get_template("oscar/customer/alerts/new_order_message.html")
    description = "Заказ №%s успешно создан!" % (ctx['number'])

    ctx['description'] = description

    Notification.objects.create(
        recipient_id=ctx['user_id'],
        order_id=ctx["order_id"],
        subject=subject,
        body=message_tpl.render(ctx).strip(), 
        description=description,
        status="Success"
    )

@shared_task()
def _notify_user_about_order_status(ctx: dict):
    
    subject = "Статус заказа изменен"
    message_tpl = loader.get_template("oscar/customer/alerts/order_status_chenged_message.html")
    description = "Новый статус заказа №%s - %s" % (ctx['number'], ctx['new_status'])

    status="Info"

    if ctx['status'] == "Отменен":
        status="Canceled"

    if ctx['status'] == "Обрабатывается" or ctx['status'] == "Ожидает оплаты":
        status="Warning"


    context = {
        'order': ctx['order'],
        'new_status': ctx['new_status'],
        'description': description
    }

    Notification.objects.create(
        recipient_id=ctx['user_id'],
        order_id=ctx["order_id"],
        subject=subject,
        body=message_tpl.render(context).strip(),
        description=description,
        status=status,
    )
    