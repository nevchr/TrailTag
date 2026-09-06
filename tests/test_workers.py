from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image

from src.geotagger.gpx_parser import TrackPoint
from src.geotagger.preview import PreviewResult
from src.geotagger.workers import PreviewWorker, ProcessingWorker


def _matched_preview(path: Path) -> PreviewResult:
    capture_time = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)
    return PreviewResult(
        source_path=path,
        photo_time=capture_time.replace(tzinfo=None),
        adjusted_time=capture_time,
        latitude=43.65,
        longitude=-79.38,
        elevation=85.0,
        matched=True,
        status="Matched",
    )


def test_preview_worker_keeps_going_when_one_photo_fails(
    tmp_path,
    monkeypatch,
):
    first_photo = tmp_path / "broken.jpg"
    second_photo = tmp_path / "working.jpg"
    first_photo.write_bytes(b"broken")
    second_photo.write_bytes(b"working")
    track = [
        TrackPoint(
            43.65,
            -79.38,
            85.0,
            datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc),
        )
    ]
    monkeypatch.setattr(
        "src.geotagger.workers.load_gpx",
        lambda path: track,
    )

    def preview_one(source_path, **kwargs):
        del kwargs
        if source_path == first_photo:
            raise ValueError("damaged metadata")
        return _matched_preview(source_path)

    monkeypatch.setattr("src.geotagger.workers.preview_photo", preview_one)
    worker = PreviewWorker(
        gpx_path=tmp_path / "route.gpx",
        photo_folder=tmp_path,
        timezone_name="UTC",
        time_offset=timedelta(),
        max_interpolation_gap=timedelta(minutes=5),
    )
    batches = []
    progress = []
    worker.completed.connect(batches.append)
    worker.progress.connect(
        lambda current, total, name: progress.append((current, total, name))
    )

    worker.run()

    assert len(batches) == 1
    assert len(batches[0].preview_results) == 2
    assert batches[0].preview_results[0].status.startswith("Preview failed:")
    assert batches[0].preview_results[1].matched is True
    assert [item[0] for item in progress] == [0, 1, 2]


def test_preview_worker_cancels_between_photos(tmp_path, monkeypatch):
    for name in ("one.jpg", "two.jpg"):
        (tmp_path / name).write_bytes(b"photo")
    track = [
        TrackPoint(
            43.65,
            -79.38,
            85.0,
            datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc),
        )
    ]
    monkeypatch.setattr(
        "src.geotagger.workers.load_gpx",
        lambda path: track,
    )
    monkeypatch.setattr(
        "src.geotagger.workers.preview_photo",
        lambda source_path, **kwargs: _matched_preview(source_path),
    )
    worker = PreviewWorker(
        gpx_path=tmp_path / "route.gpx",
        photo_folder=tmp_path,
        timezone_name="UTC",
        time_offset=timedelta(),
        max_interpolation_gap=timedelta(minutes=5),
    )
    completed = []
    cancelled = []
    worker.completed.connect(completed.append)
    worker.cancelled.connect(cancelled.append)
    worker.progress.connect(
        lambda current, total, name: worker.cancel()
        if current == 1
        else None
    )

    worker.run()

    assert completed == []
    assert cancelled == [None]


def test_processing_worker_reports_failure_and_finishes_other_photos(tmp_path):
    missing = _matched_preview(tmp_path / "missing.jpg")
    valid_path = tmp_path / "valid.jpg"
    Image.new("RGB", (8, 8), "green").save(valid_path, "JPEG")
    valid = _matched_preview(valid_path)
    output_folder = tmp_path / "output"
    worker = ProcessingWorker(
        preview_results=[missing, valid],
        output_folder=output_folder,
    )
    completed = []
    worker.completed.connect(completed.append)

    worker.run()

    assert len(completed) == 1
    assert [result.success for result in completed[0]] == [False, True]
    assert completed[0][0].status.startswith("Write failed:")
    assert (output_folder / "valid.jpg").exists()
