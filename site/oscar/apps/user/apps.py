from oscar.core.application import OscarConfig


class UserConfig(OscarConfig):
    label = "user"
    name = "oscar.apps.user"
    verbose_name = "Пользователь"

    namespace = "user"
