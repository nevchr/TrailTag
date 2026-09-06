from datetime import datetime, timedelta, timezone

from src.geotagger.gpx_parser import load_gpx
from src.geotagger.time_utils import normalize_photo_time


def test_load_gpx_sorts_points_and_skips_missing_timestamps(tmp_path):
    gpx_path = tmp_path / "track.gpx"
    gpx_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="TrailTag tests"
     xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="45.2" lon="-75.2"><time>2026-01-01T15:00:30Z</time></trkpt>
    <trkpt lat="45.9" lon="-75.9"></trkpt>
    <trkpt lat="45.1" lon="-75.1">
      <ele>100.5</ele><time>2026-01-01T15:00:00Z</time>
    </trkpt>
  </trkseg></trk>
</gpx>
""",
        encoding="utf-8",
    )

    points = load_gpx(gpx_path)

    assert len(points) == 2
    assert points[0].latitude == 45.1
    assert points[0].elevation == 100.5
    assert points[1].latitude == 45.2
    assert points[0].time < points[1].time


def test_normalize_photo_time_converts_local_time_to_utc():
    local_camera_time = datetime(2026, 1, 1, 10, 0, 0)

    result = normalize_photo_time(
        local_camera_time,
        timezone_name="America/Toronto",
    )

    assert result == datetime(2026, 1, 1, 15, 0, 0, tzinfo=timezone.utc)


def test_normalize_photo_time_applies_camera_offset():
    local_camera_time = datetime(2026, 1, 1, 10, 0, 0)

    result = normalize_photo_time(
        local_camera_time,
        timezone_name="America/Toronto",
        offset=timedelta(seconds=30),
    )

    assert result == datetime(2026, 1, 1, 15, 0, 30, tzinfo=timezone.utc)
