class YandexError(Exception):
    pass


class UnexpectedResponse(YandexError):
    pass


class InvalidKey(YandexError):
    pass


class NothingFound(YandexError):
    pass
