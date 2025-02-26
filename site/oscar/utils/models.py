import datetime
import posixpath

from django.conf import settings


def get_image_categories_upload_path(instance, filename):
    return posixpath.join(
        datetime.datetime.now().strftime(settings.OSCAR_IMAGE_CATEGORIES_FOLDER),
        filename,
    )


def get_image_products_upload_path(instance, filename):
    return posixpath.join(
        datetime.datetime.now().strftime(settings.OSCAR_IMAGE_PRODUCTS_FOLDER), filename
    )


def get_image_additionals_upload_path(instance, filename):
    return posixpath.join(
        datetime.datetime.now().strftime(settings.OSCAR_IMAGE_ADDITIONALS_FOLDER),
        filename,
    )


def get_image_actions_upload_path(instance, filename):
    return posixpath.join(
        datetime.datetime.now().strftime(settings.OSCAR_IMAGE_ACTIONS_FOLDER), filename
    )


def get_image_promocategory_upload_path(instance, filename):
    return posixpath.join(
        datetime.datetime.now().strftime(settings.OSCAR_IMAGE_PROMOCATEGORIES_FOLDER),
        filename,
    )

def get_image_offers_upload_path(instance, filename):
    return posixpath.join(
        datetime.datetime.now().strftime(settings.OSCAR_IMAGE_OFFERS_FOLDER),
        filename,
    )