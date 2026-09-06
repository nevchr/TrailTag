import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from .geo_utils import distance_metres
from .gpx_parser import TrackPoint
from .preview import PreviewResult


STORE_VERSION = 1


class TripStoreError(RuntimeError):
    """Raised when saved trips cannot be read or written safely."""


@dataclass
class SavedTrip:
    trip_id: str
    name: str
    saved_at: datetime
    gpx_path: Path | None
    photo_folder: Path | None
    output_folder: Path | None
    timezone_name: str
    time_offset_seconds: int
    max_gap_minutes: int
    track_points: list[TrackPoint]
    preview_results: list[PreviewResult]

    @property
    def distance_metres(self) -> float:
        return sum(
            distance_metres(
                first.latitude,
                first.longitude,
                second.latitude,
                second.longitude,
            )
            for first, second in zip(
                self.track_points,
                self.track_points[1:],
            )
        )

    @property
    def start_time(self) -> datetime | None:
        if not self.track_points:
            return None
        return self.track_points[0].time

    @property
    def end_time(self) -> datetime | None:
        if not self.track_points:
            return None
        return self.track_points[-1].time

    @property
    def duration(self) -> timedelta:
        if self.start_time is None or self.end_time is None:
            return timedelta()
        return max(self.end_time - self.start_time, timedelta())

    @property
    def matched_photo_count(self) -> int:
        return sum(result.matched for result in self.preview_results)

    @property
    def elevation_gain_metres(self) -> float | None:
        elevation_pairs = [
            (first.elevation, second.elevation)
            for first, second in zip(
                self.track_points,
                self.track_points[1:],
            )
            if first.elevation is not None and second.elevation is not None
        ]
        if not elevation_pairs:
            return None
        return sum(
            max(0.0, second - first)
            for first, second in elevation_pairs
        )

    @property
    def average_speed_kmh(self) -> float | None:
        hours = self.duration.total_seconds() / 3_600
        if hours <= 0:
            return None
        return (self.distance_metres / 1000) / hours


def default_trip_store_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "TrailTag" / "trips.json"
    return Path.home() / ".trailtag" / "trips.json"


def create_saved_trip(
    *,
    name: str,
    gpx_path: Path | None,
    photo_folder: Path | None,
    output_folder: Path | None,
    timezone_name: str,
    time_offset_seconds: int,
    max_gap_minutes: int,
    track_points: list[TrackPoint],
    preview_results: list[PreviewResult],
) -> SavedTrip:
    return SavedTrip(
        trip_id=str(uuid4()),
        name=name.strip(),
        saved_at=datetime.now(timezone.utc),
        gpx_path=gpx_path,
        photo_folder=photo_folder,
        output_folder=output_folder,
        timezone_name=timezone_name,
        time_offset_seconds=time_offset_seconds,
        max_gap_minutes=max_gap_minutes,
        track_points=list(track_points),
        preview_results=list(preview_results),
    )


class TripStore:
    def __init__(self, path: Path | None = None):
        self.path = path or default_trip_store_path()

    def load_trips(self) -> list[SavedTrip]:
        if not self.path.exists():
            return []

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("invalid saved-trip format")
            if payload.get("version") != STORE_VERSION:
                raise ValueError("unsupported saved-trip format")

            trip_payloads = payload.get("trips", [])
            if not isinstance(trip_payloads, list):
                raise ValueError("invalid saved-trip list")
            trips = [
                _trip_from_dict(trip_payload)
                for trip_payload in trip_payloads
            ]
        except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            raise TripStoreError(
                "TrailTag could not read the saved trips file. "
                "The existing file was left unchanged."
            ) from error

        return sorted(
            trips,
            key=lambda trip: trip.saved_at,
            reverse=True,
        )

    def save_trip(self, trip: SavedTrip) -> None:
        if not trip.name:
            raise TripStoreError("A trip name is required.")

        trips = self.load_trips()
        trips = [
            existing
            for existing in trips
            if existing.trip_id != trip.trip_id
        ]
        trips.append(trip)
        trips.sort(key=lambda item: item.saved_at, reverse=True)

        self._write_trips(trips)

    def delete_trip(self, trip_id: str) -> bool:
        trips = self.load_trips()
        remaining_trips = [
            trip for trip in trips if trip.trip_id != trip_id
        ]
        if len(remaining_trips) == len(trips):
            return False

        self._write_trips(remaining_trips)
        return True

    def _write_trips(self, trips: list[SavedTrip]) -> None:

        payload = {
            "version": STORE_VERSION,
            "trips": [_trip_to_dict(item) for item in trips],
        }

        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path.write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8",
            )
            temporary_path.replace(self.path)
        except OSError as error:
            raise TripStoreError(
                "TrailTag could not update Saved trips. "
                "No existing trips were changed."
            ) from error


def _trip_to_dict(trip: SavedTrip) -> dict:
    return {
        "id": trip.trip_id,
        "name": trip.name,
        "saved_at": _datetime_to_text(trip.saved_at),
        "gpx_path": _path_to_text(trip.gpx_path),
        "photo_folder": _path_to_text(trip.photo_folder),
        "output_folder": _path_to_text(trip.output_folder),
        "timezone_name": trip.timezone_name,
        "time_offset_seconds": trip.time_offset_seconds,
        "max_gap_minutes": trip.max_gap_minutes,
        "track_points": [
            {
                "latitude": point.latitude,
                "longitude": point.longitude,
                "elevation": point.elevation,
                "time": _datetime_to_text(point.time),
            }
            for point in trip.track_points
        ],
        "preview_results": [
            {
                "source_path": str(result.source_path),
                "photo_time": _datetime_to_text(result.photo_time),
                "adjusted_time": _datetime_to_text(result.adjusted_time),
                "latitude": result.latitude,
                "longitude": result.longitude,
                "elevation": result.elevation,
                "matched": result.matched,
                "status": result.status,
            }
            for result in trip.preview_results
        ],
    }


def _trip_from_dict(payload: dict) -> SavedTrip:
    if not isinstance(payload, dict):
        raise ValueError("invalid saved trip")
    return SavedTrip(
        trip_id=str(payload["id"]),
        name=str(payload["name"]),
        saved_at=_required_datetime(payload["saved_at"]),
        gpx_path=_path_from_text(payload.get("gpx_path")),
        photo_folder=_path_from_text(payload.get("photo_folder")),
        output_folder=_path_from_text(payload.get("output_folder")),
        timezone_name=str(payload["timezone_name"]),
        time_offset_seconds=int(payload["time_offset_seconds"]),
        max_gap_minutes=int(payload["max_gap_minutes"]),
        track_points=[
            TrackPoint(
                latitude=float(point["latitude"]),
                longitude=float(point["longitude"]),
                elevation=(
                    None
                    if point.get("elevation") is None
                    else float(point["elevation"])
                ),
                time=_required_datetime(point["time"]),
            )
            for point in payload["track_points"]
        ],
        preview_results=[
            PreviewResult(
                source_path=Path(result["source_path"]),
                photo_time=_optional_datetime(result.get("photo_time")),
                adjusted_time=_optional_datetime(result.get("adjusted_time")),
                latitude=(
                    None
                    if result.get("latitude") is None
                    else float(result["latitude"])
                ),
                longitude=(
                    None
                    if result.get("longitude") is None
                    else float(result["longitude"])
                ),
                elevation=(
                    None
                    if result.get("elevation") is None
                    else float(result["elevation"])
                ),
                matched=bool(result["matched"]),
                status=str(result["status"]),
            )
            for result in payload["preview_results"]
        ],
    )


def _datetime_to_text(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _required_datetime(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("missing saved-trip date")
    return datetime.fromisoformat(value)


def _optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    return _required_datetime(value)


def _path_to_text(value: Path | None) -> str | None:
    return str(value) if value is not None else None


def _path_from_text(value: object) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("invalid saved-trip path")
    return Path(value)
