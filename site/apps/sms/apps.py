from django.urls import include, path
from core.application import Config
from django.db import connection


class SmsConfig(Config):
    name = "apps.sms"
    verbose_name = "СМС и Аутентификация"
    namespace = "sms"

    def ready(self):
        from celery import current_app
        from django_celery_beat.models import IntervalSchedule, PeriodicTask

        if current_app.loader:
            try:
                # Проверяем, существуют ли таблицы в базе данных
                table_names = connection.introspection.table_names()
                if (
                    "django_celery_beat_intervalschedule" in table_names
                    and "django_celery_beat_periodictask" in table_names
                ):
                    # Создаем или получаем IntervalSchedule
                    schedule, created = IntervalSchedule.objects.get_or_create(
                        every=1,
                        period=IntervalSchedule.HOURS,
                    )

                    # Создаем или получаем PeriodicTask
                    PeriodicTask.objects.get_or_create(
                        interval=schedule,
                        name="Удалить неактуальные СМС регистрации",
                        task="sms.tasks.clear_expired",
                    )
                else:
                    print("Таблицы для django_celery_beat не найдены.")
            except Exception as e:
                print("Ошибка при проверке базы данных:", e)

    def get_urls(self):
        urls = [path("", include("apps.sms.api.urls"), name="sms")]
        return self.post_process_urls(urls)
