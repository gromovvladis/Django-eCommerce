# Generated by Django 4.2.11 on 2025-03-20 09:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('catalogue', '0002_initial'),
        ('communication', '0002_initial'),
        ('store', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('order', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='store',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='store.store', verbose_name='Магазин'),
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AddField(
            model_name='lineprice',
            name='line',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prices', to='order.line', verbose_name='Позиция'),
        ),
        migrations.AddField(
            model_name='lineprice',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='line_prices', to='order.order', verbose_name='Опция'),
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='additional',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='line_additionals', to='catalogue.additional', verbose_name='Доп. товар'),
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='line',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='order.line', verbose_name='Позиция'),
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='option',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='line_attributes', to='catalogue.option', verbose_name='Опция'),
        ),
        migrations.AddField(
            model_name='line',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='order.order', verbose_name='Заказ'),
        ),
        migrations.AddField(
            model_name='line',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalogue.product', verbose_name='Товар'),
        ),
        migrations.AddField(
            model_name='line',
            name='stockrecord',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.stockrecord', verbose_name='Товарная запись'),
        ),
        migrations.AddField(
            model_name='line',
            name='store',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_lines', to='store.store', verbose_name='Магазин'),
        ),
        migrations.AddField(
            model_name='communicationevent',
            name='event_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='communication.communicationeventtype', verbose_name='Тип события'),
        ),
        migrations.AddField(
            model_name='communicationevent',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='communication_events', to='order.order', verbose_name='Заказ'),
        ),
        migrations.AlterUniqueTogether(
            name='shippingeventquantity',
            unique_together={('event', 'line')},
        ),
        migrations.AlterUniqueTogether(
            name='paymenteventquantity',
            unique_together={('event', 'line')},
        ),
    ]
