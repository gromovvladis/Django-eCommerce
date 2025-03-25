class MapError(Exception):
    pass


class UnexpectedResponse(MapError):
    pass


class InvalidKey(MapError):
    pass


class NothingFound(MapError):
    pass
