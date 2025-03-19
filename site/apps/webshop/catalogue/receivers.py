from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from core.loading import get_model
from core.thumbnails import get_thumbnailer

Category = get_model("catalogue", "Category")
Additional = get_model("catalogue", "Additional")
ProductImage = get_model("catalogue", "ProductImage")
PromoCategory = get_model("action", "PromoCategory")
Action = get_model("action", "Action")


# pylint: disable=unused-argument
def delete_image_files(sender, instance, **kwargs):
    """
    Deletes the original image and created thumbnails.
    """
    image_fields = (models.ImageField,)
    thumbnailer = get_thumbnailer()
    for field in instance._meta.fields:
        if isinstance(field, image_fields):
            # Make Django return ImageFieldFile instead of ImageField
            field_file = getattr(instance, field.name)
            thumbnailer.delete_thumbnails(field_file)


# Connect for all models with ImageFields - add as needed
models_with_images = [ProductImage, Category, Additional, PromoCategory, Action]
for image_instance in models_with_images:
    post_delete.connect(delete_image_files, sender=image_instance)


# pylint: disable=unused-argument
@receiver(post_save, sender=Category, dispatch_uid="set_ancestors_are_public")
def post_save_set_ancestors_are_public(sender, instance, **kwargs):
    if kwargs.get("raw"):
        return

    instance.set_ancestors_are_public()
