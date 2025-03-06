from oscar.core.application import OscarConfig


class SettingsConfig(OscarConfig):
    label = "settings"
    name = "oscar.apps.settings"
    verbose_name = "Настройки"

    namespace = "settings"
