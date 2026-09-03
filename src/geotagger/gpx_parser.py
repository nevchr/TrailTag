from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import gpxpy


@dataclass
class TrackPoint:
    latitude: float
    longitude: float
    elevation: float | None
    time: datetime


def load_gpx(file_path: Path) -> list[TrackPoint]:
    """
    Load timestamped track points from a GPX file.
    """

    with file_path.open("r", encoding="utf-8") as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    points: list[TrackPoint] = []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:

                # A timestamp is required for photo matching.
                if point.time is None:
                    continue

                points.append(
                    TrackPoint(
                        latitude=point.latitude,
                        longitude=point.longitude,
                        elevation=point.elevation,
                        time=point.time,
                    )
                )

    points.sort(key=lambda point: point.time)

    return points