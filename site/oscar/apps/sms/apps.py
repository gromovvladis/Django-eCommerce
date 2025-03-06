from django.urls import include, path

from oscar.core.application import OscarConfig


class SmsConfig(OscarConfig):
    name = "oscar.apps.sms"
    verbose_name = "СМС и Аутентификация"
    namespace = "sms"

    def ready(self):
        from celery import current_app
        from django_celery_beat.models import PeriodicTask, IntervalSchedule

        if current_app.loader:
            schedule = IntervalSchedule.objects.get_or_create(
                every=1,
                period=IntervalSchedule.HOURS,
            )[0]

            PeriodicTask.objects.get_or_create(
                interval=schedule,
                name="Удалить неактуальные СМС регистрации",
                task="sms.tasks.clear_expired",
            )

    def get_urls(self):
        urls = [path("", include("oscar.apps.sms.api.urls"), name="sms")]
        return self.post_process_urls(urls)
