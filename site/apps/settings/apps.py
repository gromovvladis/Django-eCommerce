from core.application import Config


class SettingsConfig(Config):
    label = "settings"
    name = "apps.settings"
    verbose_name = "Настройки"

    namespace = "settings"
