from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from .gpx_parser import TrackPoint
from .matcher import match_photo_to_track
from .photo_metadata import read_photo_time
from .time_utils import normalize_photo_time


@dataclass
class PreviewResult:
    source_path: Path
    photo_time: datetime | None
    adjusted_time: datetime | None
    latitude: float | None
    longitude: float | None
    elevation: float | None
    matched: bool
    status: str


def preview_photo(
    source_path: Path,
    track_points: list[TrackPoint],
    timezone_name: str,
    time_offset: timedelta,
    max_interpolation_gap: timedelta,
) -> PreviewResult:
    """
    Calculate where a photo should be geotagged
    without modifying the photo.
    """

    photo_time = read_photo_time(source_path)

    if photo_time is None:
        return PreviewResult(
            source_path=source_path,
            photo_time=None,
            adjusted_time=None,
            latitude=None,
            longitude=None,
            elevation=None,
            matched=False,
            status="No EXIF capture time",
        )

    adjusted_time = normalize_photo_time(
        photo_time,
        timezone_name=timezone_name,
        offset=time_offset,
    )

    match = match_photo_to_track(
        adjusted_time,
        track_points,
        max_interpolation_gap=max_interpolation_gap,
    )

    if match is None:
        return PreviewResult(
            source_path=source_path,
            photo_time=photo_time,
            adjusted_time=adjusted_time,
            latitude=None,
            longitude=None,
            elevation=None,
            matched=False,
            status="No GPX match",
        )

    return PreviewResult(
        source_path=source_path,
        photo_time=photo_time,
        adjusted_time=adjusted_time,
        latitude=match.latitude,
        longitude=match.longitude,
        elevation=match.elevation,
        matched=True,
        status="Matched",
    )


def preview_folder(
    photo_folder: Path,
    track_points: list[TrackPoint],
    timezone_name: str,
    time_offset: timedelta,
    max_interpolation_gap: timedelta,
) -> list[PreviewResult]:
    """
    Preview all supported JPEG photos in a folder.
    No files are modified.
    """

    photo_files = sorted(
        path
        for path in photo_folder.iterdir()
        if path.suffix.lower() in {".jpg", ".jpeg"}
    )

    return [
        preview_photo(
            source_path=photo_path,
            track_points=track_points,
            timezone_name=timezone_name,
            time_offset=time_offset,
            max_interpolation_gap=max_interpolation_gap,
        )
        for photo_path in photo_files
    ]