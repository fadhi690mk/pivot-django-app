"""
Convert uploaded images to WebP on save.
"""
import os
import uuid
from io import BytesIO
from django.db.models import ImageField
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


def convert_image_to_webp(instance, field_name: str) -> bool:
    """
    If the given ImageField on instance has a file that is not WebP,
    convert it to WebP, update the field, and delete the old file.
    Returns True if conversion was performed.
    """
    try:
        field = instance._meta.get_field(field_name)
    except Exception:
        return False
    if not isinstance(field, ImageField):
        return False
    file_obj = getattr(instance, field_name, None)
    if not file_obj or not file_obj.name:
        return False
    path = file_obj.name
    if path.lower().endswith(".webp"):
        return False
    try:
        from PIL import Image
    except ImportError:
        return False

    storage = file_obj.storage
    full_path = getattr(file_obj, "path", None)
    if not full_path or not os.path.isfile(full_path):
        return False

    try:
        with Image.open(full_path) as img:
            rgb = img.convert("RGB") if img.mode not in ("RGB", "RGBA") else img
            buf = BytesIO()
            save_kw = {"format": "WEBP", "quality": 85}
            if rgb.mode == "RGBA":
                save_kw["lossless"] = False
            rgb.save(buf, **save_kw)
            buf.seek(0)
            base, _ = os.path.splitext(path)
            webp_name = base + ".webp"
            storage.save(webp_name, buf)
        setattr(instance, field_name, webp_name)
        instance.save(update_fields=[field_name])
        if storage.exists(path):
            storage.delete(path)
        return True
    except Exception:
        return False


def save_uploaded_image_as_webp(uploaded_file, upload_to: str = "hero/"):
    """
    Save an uploaded image file to default storage as WebP.
    Returns the relative path (e.g. "hero/abc123.webp") for use in ImageField.
    """
    try:
        from PIL import Image
    except ImportError:
        ext = os.path.splitext(uploaded_file.name)[1] or ".jpg"
        name = f"{upload_to.rstrip('/')}/{uuid.uuid4().hex}{ext}"
        default_storage.save(name, uploaded_file)
        return name

    raw_name = f"{uuid.uuid4().hex}_{uploaded_file.name}"
    temp_path = f"{upload_to.rstrip('/')}/{raw_name}"
    default_storage.save(temp_path, uploaded_file)

    try:
        with default_storage.open(temp_path, "rb") as f:
            with Image.open(f) as fh:
                rgb = fh.convert("RGB") if fh.mode not in ("RGB", "RGBA") else fh
                buf = BytesIO()
                save_kw = {"format": "WEBP", "quality": 85}
                if rgb.mode == "RGBA":
                    save_kw["lossless"] = False
                rgb.save(buf, **save_kw)
                buf.seek(0)
                base, _ = os.path.splitext(raw_name)
                webp_name = f"{upload_to.rstrip('/')}/{base}.webp"
                default_storage.save(webp_name, ContentFile(buf.getvalue()))
        if default_storage.exists(temp_path):
            default_storage.delete(temp_path)
        return webp_name
    except Exception:
        if default_storage.exists(temp_path):
            default_storage.delete(temp_path)
        raise
