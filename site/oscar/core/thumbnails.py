from django.apps import apps
from django.conf import settings
from django.utils.module_loading import import_string


class Thumbnailer(object):
    def generate_thumbnail(self, source, **opts):
        raise NotImplementedError

    def delete_thumbnails(self, source):
        raise NotImplementedError


class SorlThumbnail(Thumbnailer):
    def __init__(self):
        if not apps.is_installed("sorl.thumbnail"):
            raise ValueError('"sorl.thumbnail" is not listed in "INSTALLED_APPS".')

    def generate_thumbnail(self, source, **opts):
        from sorl.thumbnail import get_thumbnail

        # Sorl can accept only: "width x height", "width", "x height".
        # https://sorl-thumbnail.readthedocs.io/en/latest/template.html#geometry
        # So for example value '50x' must be converted to '50'.
        size = opts.pop("size")
        width, height = size.split("x")
        # Set `size` to `width` if `height` is not provided.
        size = size if height else width
        return get_thumbnail(source, size, **opts)

    def delete_thumbnails(self, source):
        from sorl.thumbnail import delete
        from sorl.thumbnail.helpers import ThumbnailError

        try:
            delete(source)
        except ThumbnailError:
            pass


def get_thumbnailer():
    thumbnailer = import_string(settings.OSCAR_THUMBNAILER)
    return thumbnailer()
