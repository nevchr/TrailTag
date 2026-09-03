from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def normalize_photo_time(
    photo_time: datetime,
    timezone_name: str = "America/Toronto",
    offset: timedelta = timedelta(0),
) -> datetime:
    """
    Convert a camera's timezone-naive EXIF timestamp into
    a timezone-aware UTC timestamp.

    The offset is added to the photo time before matching.
    """

    local_timezone = ZoneInfo(timezone_name)

    localized_time = photo_time.replace(
        tzinfo=local_timezone
    )

    adjusted_time = localized_time + offset

    return adjusted_time.astimezone(
        ZoneInfo("UTC")
    )