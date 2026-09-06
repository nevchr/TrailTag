import base64
from io import BytesIO

from PIL import Image

from src.geotagger.image_preview import create_photo_preview_data_uri


def test_creates_bounded_jpeg_preview(tmp_path):
    photo_path = tmp_path / "large-photo.jpg"
    Image.new(
        "RGB",
        (900, 600),
        color="cornflowerblue",
    ).save(photo_path, format="JPEG")

    data_uri = create_photo_preview_data_uri(photo_path)

    assert data_uri is not None
    prefix, encoded_image = data_uri.split(",", maxsplit=1)
    assert prefix == "data:image/jpeg;base64"

    with Image.open(BytesIO(base64.b64decode(encoded_image))) as preview:
        assert preview.format == "JPEG"
        assert preview.size == (360, 240)


def test_returns_none_when_photo_cannot_be_previewed(tmp_path):
    invalid_photo = tmp_path / "invalid.jpg"
    invalid_photo.write_text("not an image", encoding="utf-8")

    assert create_photo_preview_data_uri(invalid_photo) is None
