from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.geotagger.gpx_parser import TrackPoint
from src.geotagger.preview import PreviewResult
from src.geotagger.trip_store import (
    TripStore,
    TripStoreError,
    create_saved_trip,
)


def _sample_trip():
    start = datetime(2026, 9, 4, 13, 0, tzinfo=timezone.utc)
    track_points = [
        TrackPoint(43.6500, -79.3800, 80.0, start),
        TrackPoint(
            43.6600,
            -79.3800,
            92.0,
            start + timedelta(hours=1, minutes=15),
        ),
    ]
    preview_results = [
        PreviewResult(
            source_path=Path("photos/trail.jpg"),
            photo_time=datetime(2026, 9, 4, 9, 30),
            adjusted_time=start + timedelta(minutes=30),
            latitude=43.654,
            longitude=-79.38,
            elevation=85.0,
            matched=True,
            status="Matched",
        )
    ]
    return create_saved_trip(
        name="Toronto waterfront",
        gpx_path=Path("routes/waterfront.gpx"),
        photo_folder=Path("photos"),
        output_folder=Path("tagged"),
        timezone_name="America/Toronto",
        time_offset_seconds=30,
        max_gap_minutes=5,
        track_points=track_points,
        preview_results=preview_results,
    )


def test_saved_trip_survives_store_reload(tmp_path):
    store_path = tmp_path / "TrailTag" / "trips.json"
    store = TripStore(store_path)
    trip = _sample_trip()

    store.save_trip(trip)
    reloaded = TripStore(store_path).load_trips()

    assert len(reloaded) == 1
    assert reloaded[0].trip_id == trip.trip_id
    assert reloaded[0].name == "Toronto waterfront"
    assert reloaded[0].timezone_name == "America/Toronto"
    assert reloaded[0].time_offset_seconds == 30
    assert reloaded[0].track_points == trip.track_points
    assert reloaded[0].preview_results == trip.preview_results
    assert reloaded[0].duration == timedelta(hours=1, minutes=15)
    assert reloaded[0].matched_photo_count == 1
    assert 1100 < reloaded[0].distance_metres < 1120
    assert reloaded[0].elevation_gain_metres == 12.0
    assert reloaded[0].average_speed_kmh == pytest.approx(0.89, abs=0.02)


def test_store_keeps_multiple_named_trips_newest_first(tmp_path):
    store = TripStore(tmp_path / "trips.json")
    older = _sample_trip()
    newer = _sample_trip()
    older.name = "Morning walk"
    newer.name = "Evening walk"
    older.saved_at = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)
    newer.saved_at = datetime(2026, 9, 4, 18, 0, tzinfo=timezone.utc)

    store.save_trip(older)
    store.save_trip(newer)

    assert [trip.name for trip in store.load_trips()] == [
        "Evening walk",
        "Morning walk",
    ]


def test_corrupt_store_is_not_overwritten(tmp_path):
    store_path = tmp_path / "trips.json"
    store_path.write_text("not valid json", encoding="utf-8")
    store = TripStore(store_path)

    with pytest.raises(TripStoreError):
        store.save_trip(_sample_trip())

    assert store_path.read_text(encoding="utf-8") == "not valid json"


def test_saved_trip_can_be_deleted_without_touching_source_files(tmp_path):
    source_photo = tmp_path / "trail.jpg"
    source_photo.write_bytes(b"original photo")
    trip = _sample_trip()
    trip.preview_results[0].source_path = source_photo
    store = TripStore(tmp_path / "trips.json")
    store.save_trip(trip)

    assert store.delete_trip(trip.trip_id) is True

    assert store.load_trips() == []
    assert source_photo.read_bytes() == b"original photo"
