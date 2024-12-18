from django.urls import include, path

from oscar.core.application import OscarConfig


class SmsConfig(OscarConfig):
    name = "oscar.apps.sms_auth"
    verbose_name = "СМС Аутентификация"
    namespace = "sms_auth"

    def ready(self):
        from django_celery_beat.models import PeriodicTask, IntervalSchedule
        from celery import current_app

        if current_app.loader:
            schedule = IntervalSchedule.objects.get_or_create(
                every=1,
                period=IntervalSchedule.HOURS,
            )[0]

            PeriodicTask.objects.get_or_create(
                interval=schedule,
                name="Удалить неактуальные СМС",
                task="sms_auth.tasks.clear_expired",
            )

    def get_urls(self):
        urls = [
            path('', include('oscar.apps.sms_auth.api.urls'), name='sms_auth')
        ]
        return self.post_process_urls(urls)