from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from threading import Event
from zoneinfo import ZoneInfo

from PySide6.QtCore import QObject, Signal, Slot

from .gpx_parser import TrackPoint, load_gpx
from .preview import PreviewResult, preview_photo
from .processor import (
    ProcessResult,
    process_preview_result,
    validate_output_folder,
)


@dataclass
class PreviewBatch:
    track_points: list[TrackPoint]
    preview_results: list[PreviewResult]


class PreviewWorker(QObject):
    progress = Signal(int, int, str)
    completed = Signal(object)
    cancelled = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        *,
        gpx_path: Path,
        photo_folder: Path,
        timezone_name: str,
        time_offset: timedelta,
        max_interpolation_gap: timedelta,
    ):
        super().__init__()
        self.gpx_path = gpx_path
        self.photo_folder = photo_folder
        self.timezone_name = timezone_name
        self.time_offset = time_offset
        self.max_interpolation_gap = max_interpolation_gap
        self._cancel_event = Event()

    def cancel(self) -> None:
        self._cancel_event.set()

    @Slot()
    def run(self) -> None:
        try:
            track_points = load_gpx(self.gpx_path)
            if not track_points:
                raise ValueError(
                    "The GPX file contains no timestamped track points."
                )

            ZoneInfo(self.timezone_name)

            photo_files = sorted(
                path
                for path in self.photo_folder.iterdir()
                if path.suffix.lower() in {".jpg", ".jpeg"}
            )
            total = len(photo_files)
            results: list[PreviewResult] = []
            self.progress.emit(0, total, "Preparing photos")

            for current, photo_path in enumerate(photo_files, start=1):
                if self._cancel_event.is_set():
                    self.cancelled.emit(None)
                    return

                try:
                    result = preview_photo(
                        source_path=photo_path,
                        track_points=track_points,
                        timezone_name=self.timezone_name,
                        time_offset=self.time_offset,
                        max_interpolation_gap=self.max_interpolation_gap,
                    )
                except Exception as error:
                    result = PreviewResult(
                        source_path=photo_path,
                        photo_time=None,
                        adjusted_time=None,
                        latitude=None,
                        longitude=None,
                        elevation=None,
                        matched=False,
                        status=f"Preview failed: {error}",
                    )

                results.append(result)
                self.progress.emit(current, total, photo_path.name)

            if self._cancel_event.is_set():
                self.cancelled.emit(None)
                return

            self.completed.emit(PreviewBatch(track_points, results))
        except Exception as error:
            self.failed.emit(str(error))


class ProcessingWorker(QObject):
    progress = Signal(int, int, str)
    completed = Signal(object)
    cancelled = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        *,
        preview_results: list[PreviewResult],
        output_folder: Path,
    ):
        super().__init__()
        self.preview_results = list(preview_results)
        self.output_folder = output_folder
        self._cancel_event = Event()

    def cancel(self) -> None:
        self._cancel_event.set()

    @Slot()
    def run(self) -> None:
        try:
            validate_output_folder(self.preview_results, self.output_folder)
            total = len(self.preview_results)
            results: list[ProcessResult] = []
            self.progress.emit(0, total, "Preparing output")

            for current, preview in enumerate(self.preview_results, start=1):
                if self._cancel_event.is_set():
                    self.cancelled.emit(results)
                    return

                result = process_preview_result(preview, self.output_folder)
                results.append(result)
                self.progress.emit(current, total, preview.source_path.name)

            if self._cancel_event.is_set():
                self.cancelled.emit(results)
                return

            self.completed.emit(results)
        except Exception as error:
            self.failed.emit(str(error))
