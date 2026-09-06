import base64
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps


DEFAULT_PREVIEW_SIZE = (360, 240)


def create_photo_preview_data_uri(
    photo_path: Path,
    maximum_size: tuple[int, int] = DEFAULT_PREVIEW_SIZE,
) -> str | None:
    """Create a small, correctly oriented JPEG preview for the map."""

    try:
        with Image.open(photo_path) as source_image:
            preview_image = ImageOps.exif_transpose(source_image)
            preview_image.thumbnail(
                maximum_size,
                Image.Resampling.LANCZOS,
            )

            if preview_image.mode != "RGB":
                preview_image = preview_image.convert("RGB")

            buffer = BytesIO()
            preview_image.save(
                buffer,
                format="JPEG",
                quality=82,
                optimize=True,
            )
    except (OSError, ValueError, Image.DecompressionBombError):
        return None

    encoded_preview = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded_preview}"
