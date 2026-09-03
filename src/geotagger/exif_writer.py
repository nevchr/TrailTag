from pathlib import Path
from shutil import copy2

import piexif


def _decimal_to_dms(
    coordinate: float,
) -> tuple[
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
]:
    """
    Convert decimal GPS coordinates into EXIF
    degrees/minutes/seconds rational values.
    """

    coordinate = abs(coordinate)

    degrees = int(coordinate)

    minutes_float = (
        coordinate - degrees
    ) * 60

    minutes = int(minutes_float)

    seconds = (
        minutes_float - minutes
    ) * 60

    return (
        (degrees, 1),
        (minutes, 1),
        (round(seconds * 1_000_000), 1_000_000),
    )


def write_photo_gps(
    source_path: Path,
    output_path: Path,
    latitude: float,
    longitude: float,
    elevation: float | None = None,
) -> None:
    """
    Create a copy of a JPEG and write GPS metadata
    into the copy.

    The source photo is never modified.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Copy the original first.
    copy2(
        source_path,
        output_path,
    )

    # Load existing EXIF from the copied photo.
    exif_dict = piexif.load(
        str(output_path)
    )

    gps_ifd = exif_dict.get(
        "GPS",
        {},
    )

    gps_ifd[
        piexif.GPSIFD.GPSVersionID
    ] = (2, 3, 0, 0)

    gps_ifd[
        piexif.GPSIFD.GPSLatitudeRef
    ] = b"N" if latitude >= 0 else b"S"

    gps_ifd[
        piexif.GPSIFD.GPSLatitude
    ] = _decimal_to_dms(latitude)

    gps_ifd[
        piexif.GPSIFD.GPSLongitudeRef
    ] = b"E" if longitude >= 0 else b"W"

    gps_ifd[
        piexif.GPSIFD.GPSLongitude
    ] = _decimal_to_dms(longitude)

    if elevation is not None:
        gps_ifd[
            piexif.GPSIFD.GPSAltitudeRef
        ] = 0 if elevation >= 0 else 1

        gps_ifd[
            piexif.GPSIFD.GPSAltitude
        ] = (
            round(abs(elevation) * 100),
            100,
        )

    exif_dict["GPS"] = gps_ifd

    exif_bytes = piexif.dump(
        exif_dict
    )

    piexif.insert(
        exif_bytes,
        str(output_path),
    )