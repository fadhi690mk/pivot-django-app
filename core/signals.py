"""
Convert any newly saved image to WebP.
"""
from django.db.models import Model, ImageField
from django.db.models.signals import post_save
from django.apps import apps

from .image_utils import convert_image_to_webp


def convert_images_to_webp(sender, instance, **kwargs):
    if not isinstance(instance, Model):
        return
    for field in sender._meta.get_fields():
        if isinstance(field, ImageField):
            convert_image_to_webp(instance, field.name)


def connect_webp_signals():
    for model in apps.get_models():
        if any(isinstance(f, ImageField) for f in model._meta.get_fields()):
            post_save.connect(
                convert_images_to_webp,
                sender=model,
                dispatch_uid="core.webp.%s" % model.__name__,
            )
