from datetime import datetime, timedelta, timezone

import piexif
import pytest
from PIL import Image

from src.geotagger.exif_writer import write_photo_gps
from src.geotagger.gpx_parser import TrackPoint
from src.geotagger.photo_metadata import read_photo_gps, read_photo_time
from src.geotagger.preview import PreviewResult, preview_folder
from src.geotagger.processor import process_preview_results


UTC = timezone.utc


def create_jpeg(path, capture_time: str | None = None):
    image = Image.new("RGB", (8, 8), color="green")

    if capture_time is None:
        image.save(path, format="JPEG")
        return

    exif = {
        "0th": {},
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: capture_time.encode("ascii"),
        },
        "GPS": {},
        "1st": {},
        "thumbnail": None,
    }

    image.save(
        path,
        format="JPEG",
        exif=piexif.dump(exif),
    )


def test_reads_photo_capture_time(tmp_path):
    photo = tmp_path / "photo.jpg"
    create_jpeg(photo, "2026:01:01 10:00:15")

    assert read_photo_time(photo) == datetime(2026, 1, 1, 10, 0, 15)


def test_returns_none_when_photo_has_no_capture_time(tmp_path):
    photo = tmp_path / "photo.jpg"
    create_jpeg(photo)

    assert read_photo_time(photo) is None


def test_writes_gps_to_copy_without_changing_source(tmp_path):
    source = tmp_path / "source.jpg"
    output = tmp_path / "output" / "source.jpg"
    create_jpeg(source, "2026:01:01 10:00:15")
    original_bytes = source.read_bytes()

    write_photo_gps(
        source_path=source,
        output_path=output,
        latitude=45.4215,
        longitude=-75.6972,
        elevation=123.45,
    )

    assert source.read_bytes() == original_bytes
    assert read_photo_gps(source) is None

    coordinates = read_photo_gps(output)
    assert coordinates is not None
    assert coordinates[0] == pytest.approx(45.4215, abs=0.000001)
    assert coordinates[1] == pytest.approx(-75.6972, abs=0.000001)


def test_preview_folder_matches_jpegs_and_ignores_other_files(tmp_path):
    photo = tmp_path / "photo.jpg"
    create_jpeg(photo, "2026:01:01 10:00:15")
    (tmp_path / "notes.txt").write_text("not a photo", encoding="utf-8")

    track = [
        TrackPoint(
            45.0,
            -75.0,
            100.0,
            datetime(2026, 1, 1, 15, 0, 0, tzinfo=UTC),
        ),
        TrackPoint(
            46.0,
            -76.0,
            200.0,
            datetime(2026, 1, 1, 15, 0, 30, tzinfo=UTC),
        ),
    ]

    results = preview_folder(
        photo_folder=tmp_path,
        track_points=track,
        timezone_name="America/Toronto",
        time_offset=timedelta(0),
        max_interpolation_gap=timedelta(minutes=5),
    )

    assert len(results) == 1
    assert results[0].matched is True
    assert results[0].latitude == 45.5
    assert results[0].longitude == -75.5
    assert results[0].elevation == 150.0


def test_processing_geotags_matches_and_skips_unmatched_photos(tmp_path):
    source_folder = tmp_path / "source"
    source_folder.mkdir()
    matched_photo = source_folder / "matched.jpg"
    unmatched_photo = source_folder / "unmatched.jpg"
    create_jpeg(matched_photo, "2026:01:01 10:00:15")
    create_jpeg(unmatched_photo)

    previews = [
        PreviewResult(
            source_path=matched_photo,
            photo_time=datetime(2026, 1, 1, 10, 0, 15),
            adjusted_time=datetime(2026, 1, 1, 15, 0, 15, tzinfo=UTC),
            latitude=45.5,
            longitude=-75.5,
            elevation=150.0,
            matched=True,
            status="Matched",
        ),
        PreviewResult(
            source_path=unmatched_photo,
            photo_time=None,
            adjusted_time=None,
            latitude=None,
            longitude=None,
            elevation=None,
            matched=False,
            status="No EXIF capture time",
        ),
    ]

    output_folder = tmp_path / "output"
    results = process_preview_results(previews, output_folder)

    assert [result.success for result in results] == [True, False]
    assert (output_folder / "matched.jpg").exists()
    assert not (output_folder / "unmatched.jpg").exists()
    assert read_photo_gps(output_folder / "matched.jpg") == pytest.approx(
        (45.5, -75.5),
        abs=0.000001,
    )


def test_processing_rejects_source_folder_as_output(tmp_path):
    photo = tmp_path / "photo.jpg"
    create_jpeg(photo, "2026:01:01 10:00:15")

    preview = PreviewResult(
        source_path=photo,
        photo_time=datetime(2026, 1, 1, 10, 0, 15),
        adjusted_time=datetime(2026, 1, 1, 15, 0, 15, tzinfo=UTC),
        latitude=45.5,
        longitude=-75.5,
        elevation=150.0,
        matched=True,
        status="Matched",
    )

    with pytest.raises(ValueError, match="output folder must be different"):
        process_preview_results([preview], tmp_path)


def test_processing_keeps_an_existing_output_and_uses_a_numbered_name(tmp_path):
    source_folder = tmp_path / "source"
    output_folder = tmp_path / "output"
    source_folder.mkdir()
    output_folder.mkdir()
    source = source_folder / "photo.jpg"
    existing_output = output_folder / "photo.jpg"
    create_jpeg(source, "2026:01:01 10:00:15")
    existing_output.write_bytes(b"previous TrailTag result")

    preview = PreviewResult(
        source_path=source,
        photo_time=datetime(2026, 1, 1, 10, 0, 15),
        adjusted_time=datetime(2026, 1, 1, 15, 0, 15, tzinfo=UTC),
        latitude=45.5,
        longitude=-75.5,
        elevation=150.0,
        matched=True,
        status="Matched",
    )

    result = process_preview_results([preview], output_folder)[0]

    assert existing_output.read_bytes() == b"previous TrailTag result"
    assert result.success is True
    assert result.output_path == output_folder / "photo (1).jpg"
    assert result.status == "Geotagged as photo (1).jpg"
    assert read_photo_gps(result.output_path) == pytest.approx(
        (45.5, -75.5),
        abs=0.000001,
    )


def test_failed_exif_write_leaves_no_incomplete_output(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "source.jpg"
    output = tmp_path / "output" / "source.jpg"
    create_jpeg(source, "2026:01:01 10:00:15")

    def fail_insert(*args, **kwargs):
        raise RuntimeError("simulated EXIF failure")

    monkeypatch.setattr(
        "src.geotagger.exif_writer.piexif.insert",
        fail_insert,
    )

    with pytest.raises(RuntimeError, match="simulated EXIF failure"):
        write_photo_gps(
            source_path=source,
            output_path=output,
            latitude=45.5,
            longitude=-75.5,
        )

    assert not output.exists()
    assert list(output.parent.iterdir()) == []
