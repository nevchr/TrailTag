from datetime import datetime, timedelta, timezone

import pytest

from src.geotagger.geo_utils import distance_metres
from src.geotagger.gpx_parser import TrackPoint
from src.geotagger.matcher import interpolate, match_photo_to_track


UTC = timezone.utc


def point(
    second: int,
    latitude: float,
    longitude: float,
    elevation: float | None = None,
) -> TrackPoint:
    return TrackPoint(
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
        time=datetime(2026, 1, 1, 15, 0, second, tzinfo=UTC),
    )


def test_interpolate_returns_point_between_values():
    assert interpolate(10.0, 20.0, 0.25) == 12.5


def test_exact_timestamp_uses_recorded_track_point():
    track = [
        point(0, 45.0, -75.0, 100.0),
        point(30, 46.0, -76.0, 200.0),
    ]

    result = match_photo_to_track(track[0].time, track)

    assert result is not None
    assert result.latitude == 45.0
    assert result.longitude == -75.0
    assert result.elevation == 100.0
    assert result.before is result.after
    assert result.interpolation_ratio == 0.0


def test_interpolates_coordinates_and_elevation():
    track = [
        point(0, 45.0, -75.0, 100.0),
        point(30, 46.0, -76.0, 200.0),
    ]

    result = match_photo_to_track(
        datetime(2026, 1, 1, 15, 0, 15, tzinfo=UTC),
        track,
    )

    assert result is not None
    assert result.latitude == 45.5
    assert result.longitude == -75.5
    assert result.elevation == 150.0
    assert result.interpolation_ratio == 0.5


@pytest.mark.parametrize(
    "photo_time",
    [
        datetime(2026, 1, 1, 14, 59, 59, tzinfo=UTC),
        datetime(2026, 1, 1, 15, 0, 31, tzinfo=UTC),
    ],
)
def test_does_not_extrapolate_outside_track(photo_time):
    track = [
        point(0, 45.0, -75.0),
        point(30, 46.0, -76.0),
    ]

    assert match_photo_to_track(photo_time, track) is None


def test_rejects_interpolation_across_large_gap():
    track = [
        point(0, 45.0, -75.0),
        point(30, 46.0, -76.0),
    ]

    result = match_photo_to_track(
        datetime(2026, 1, 1, 15, 0, 15, tzinfo=UTC),
        track,
        max_interpolation_gap=timedelta(seconds=20),
    )

    assert result is None


def test_missing_elevation_stays_missing():
    track = [
        point(0, 45.0, -75.0, None),
        point(30, 46.0, -76.0, 200.0),
    ]

    result = match_photo_to_track(
        datetime(2026, 1, 1, 15, 0, 15, tzinfo=UTC),
        track,
    )

    assert result is not None
    assert result.elevation is None


def test_haversine_distance_is_zero_for_same_location():
    assert distance_metres(45.0, -75.0, 45.0, -75.0) == 0.0


def test_haversine_distance_is_reasonable_for_one_degree():
    distance = distance_metres(0.0, 0.0, 1.0, 0.0)

    assert distance == pytest.approx(111_195, abs=1)
