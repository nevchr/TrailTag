from datetime import datetime
from pathlib import Path

from PIL import Image, ExifTags


DATE_TIME_ORIGINAL_TAG = 36867


def read_photo_time(file_path: Path) -> datetime | None:
    """
    Read the original capture time from a photo's EXIF metadata.

    Returns None if DateTimeOriginal is unavailable.
    """

    with Image.open(file_path) as image:
        exif = image.getexif()

        if not exif:
            return None

        # Try reading DateTimeOriginal directly.
        value = exif.get(DATE_TIME_ORIGINAL_TAG)

        # Some JPEGs keep it inside the EXIF IFD instead.
        if value is None:
            try:
                exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
                value = exif_ifd.get(DATE_TIME_ORIGINAL_TAG)
            except (AttributeError, KeyError):
                value = None

        if value is None:
            return None

        try:
            return datetime.strptime(
                str(value),
                "%Y:%m:%d %H:%M:%S",
            )
        except ValueError:
            return None

def _dms_to_decimal(
    degrees: float,
    minutes: float,
    seconds: float,
    reference: str,
) -> float:
    """
    Convert EXIF GPS degrees/minutes/seconds to decimal degrees.
    """

    decimal = (
        float(degrees)
        + float(minutes) / 60
        + float(seconds) / 3600
    )

    if reference in {"S", "W"}:
        decimal *= -1

    return decimal


def read_photo_gps(
    file_path: Path,
) -> tuple[float, float] | None:
    """
    Read GPS latitude and longitude from a photo's EXIF metadata.

    Returns:
        (latitude, longitude)

    or None if GPS metadata is unavailable.
    """

    with Image.open(file_path) as image:
        exif = image.getexif()

        if not exif:
            return None

        try:
            gps_ifd = exif.get_ifd(
                ExifTags.IFD.GPSInfo
            )
        except (AttributeError, KeyError):
            return None

        if not gps_ifd:
            return None

        latitude_ref = gps_ifd.get(1)
        latitude_dms = gps_ifd.get(2)

        longitude_ref = gps_ifd.get(3)
        longitude_dms = gps_ifd.get(4)

        if (
            latitude_ref is None
            or latitude_dms is None
            or longitude_ref is None
            or longitude_dms is None
        ):
            return None

        latitude = _dms_to_decimal(
            latitude_dms[0],
            latitude_dms[1],
            latitude_dms[2],
            latitude_ref,
        )

        longitude = _dms_to_decimal(
            longitude_dms[0],
            longitude_dms[1],
            longitude_dms[2],
            longitude_ref,
        )

        return latitude, longitude