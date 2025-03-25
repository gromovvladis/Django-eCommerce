from core.application import Config


class AnalyticsConfig(Config):
    label = "analytics"
    name = "apps.webshop.analytics"
    verbose_name = "Аналитика"

    # pylint: disable=unused-import
    def ready(self):
        from . import receivers
