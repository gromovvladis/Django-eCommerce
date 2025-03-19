from core.application import Config


class UserConfig(Config):
    label = "user"
    name = "apps.webshop.user"
    verbose_name = "Пользователь"

    namespace = "user"
