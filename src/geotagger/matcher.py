from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime, timedelta
from .gpx_parser import TrackPoint


@dataclass
class MatchResult:
    latitude: float
    longitude: float
    elevation: float | None
    time: datetime
    before: TrackPoint
    after: TrackPoint
    interpolation_ratio: float


def interpolate(
    start: float,
    end: float,
    ratio: float,
) -> float:
    return start + (end - start) * ratio


def match_photo_to_track(
    photo_time: datetime,
    track_points: list[TrackPoint],
    max_interpolation_gap: timedelta | None = None,
) -> MatchResult | None:
    """
    Match a photo timestamp to the GPX track.

    If the timestamp falls between two GPX points,
    interpolate the likely location.

    If max_interpolation_gap is provided, interpolation
    is rejected when the surrounding GPX points are
    farther apart than the allowed gap.
    """

    if not track_points:
        return None

    # Never extrapolate outside the recorded track.
    if photo_time < track_points[0].time:
        return None

    if photo_time > track_points[-1].time:
        return None

    times = [
        point.time
        for point in track_points
    ]

    index = bisect_left(times, photo_time)

    # Exact timestamp match.
    if (
        index < len(track_points)
        and track_points[index].time == photo_time
    ):
        point = track_points[index]

        return MatchResult(
            latitude=point.latitude,
            longitude=point.longitude,
            elevation=point.elevation,
            time=photo_time,
            before=point,
            after=point,
            interpolation_ratio=0.0,
        )

    if index == 0 or index >= len(track_points):
        return None

    before = track_points[index - 1]
    after = track_points[index]

    gap = after.time - before.time

    # Reject unreliable interpolation across large GPX gaps.
    if (
        max_interpolation_gap is not None
        and gap > max_interpolation_gap
    ):
        return None

    total_seconds = gap.total_seconds()

    photo_seconds = (
        photo_time - before.time
    ).total_seconds()

    if total_seconds <= 0:
        return None

    ratio = photo_seconds / total_seconds

    latitude = interpolate(
        before.latitude,
        after.latitude,
        ratio,
    )

    longitude = interpolate(
        before.longitude,
        after.longitude,
        ratio,
    )

    elevation = None

    if (
        before.elevation is not None
        and after.elevation is not None
    ):
        elevation = interpolate(
            before.elevation,
            after.elevation,
            ratio,
        )

    return MatchResult(
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
        time=photo_time,
        before=before,
        after=after,
        interpolation_ratio=ratio,
    )