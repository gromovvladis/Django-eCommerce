from oscar.core.application import OscarConfig

class AnalyticsConfig(OscarConfig):
    label = "analytics"
    name = "oscar.apps.analytics"
    verbose_name = "Аналитика"

    # pylint: disable=unused-import
    def ready(self):
        from . import receivers
