"""Images téléversées : déclinaisons WebP à plusieurs largeurs (spec §7.5).

À l'enregistrement, chaque image produit des fichiers `renditions/<chemin>-<largeur>w.webp`,
jamais agrandis au-delà de l'original. La balise {% responsive_image %} les sert avec srcset,
dimensions explicites et chargement différé.
"""

from io import BytesIO
from pathlib import PurePosixPath

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageOps

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def validate_image_size(file):
    if file.size > MAX_UPLOAD_BYTES:
        raise ValidationError(_("The image must not exceed 5 MB."))


def rendition_widths(original_width, widths):
    """Largeurs réellement produites : celles plus petites que l'original, plus l'original
    plafonné à la plus grande largeur demandée."""
    if not original_width:
        return []
    largest = min(original_width, max(widths))
    return sorted({width for width in widths if width < largest} | {largest})


def rendition_name(name, width):
    return f"renditions/{PurePosixPath(name).with_suffix('')}-{width}w.webp"


def generate_renditions(field_file, widths):
    if not field_file:
        return
    storage = field_file.storage
    with field_file.open("rb") as handle:
        image = Image.open(handle)
        image.load()
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA" if image.mode in ("P", "LA", "PA") else "RGB")
    for width in rendition_widths(image.width, widths):
        name = rendition_name(field_file.name, width)
        if storage.exists(name):
            continue
        resized = image.copy()
        if resized.width > width:
            height = round(width * resized.height / resized.width)
            resized = resized.resize((width, height), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        resized.save(buffer, "WEBP", quality=82, method=6)
        storage.save(name, ContentFile(buffer.getvalue()))
