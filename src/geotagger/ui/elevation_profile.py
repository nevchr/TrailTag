from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from ..geo_utils import distance_metres
from ..gpx_parser import TrackPoint
from .theme import theme_colors


class ElevationProfile(QWidget):
    """A small, dependency-free elevation chart for a saved route."""

    def __init__(self):
        super().__init__()
        self.profile: list[tuple[float, float]] = []
        self.total_distance_metres = 0.0
        self.route_points: list[TrackPoint] = []
        self.route_distances: list[float] = []
        self.selected_distance: float | None = None
        self.setMinimumHeight(170)
        self.setToolTip("Elevation along the saved route")

    def set_track_points(self, track_points: list[TrackPoint]) -> None:
        self.profile = []
        self.route_points = list(track_points)
        self.route_distances = []
        self.selected_distance = None
        distance = 0.0

        for index, point in enumerate(track_points):
            if index:
                previous = track_points[index - 1]
                distance += distance_metres(
                    previous.latitude,
                    previous.longitude,
                    point.latitude,
                    point.longitude,
                )
            self.route_distances.append(distance)
            if point.elevation is not None:
                self.profile.append((distance, point.elevation))

        self.total_distance_metres = distance
        self.update()

    def focus_location(
        self,
        latitude: float | None,
        longitude: float | None,
    ) -> None:
        if (
            latitude is None
            or longitude is None
            or not self.route_points
        ):
            self.selected_distance = None
            self.update()
            return

        closest_index = min(
            range(len(self.route_points)),
            key=lambda index: distance_metres(
                latitude,
                longitude,
                self.route_points[index].latitude,
                self.route_points[index].longitude,
            ),
        )
        self.selected_distance = self.route_distances[closest_index]
        self.update()

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        colors = theme_colors()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(colors["surface"]))

        if len(self.profile) < 2:
            painter.setPen(QColor(colors["muted"]))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "This route does not contain enough elevation data.",
            )
            return

        chart = self.rect().adjusted(52, 20, -20, -34)
        elevations = [elevation for _, elevation in self.profile]
        minimum = min(elevations)
        maximum = max(elevations)
        elevation_range = max(maximum - minimum, 1.0)

        painter.setPen(QPen(QColor(colors["border"]), 1))
        for step in range(4):
            y = chart.top() + (chart.height() * step / 3)
            painter.drawLine(
                QPointF(chart.left(), y),
                QPointF(chart.right(), y),
            )

        first_distance = self.profile[0][0]
        last_distance = self.profile[-1][0]
        distance_range = max(last_distance - first_distance, 1.0)
        plotted_points = []

        for distance, elevation in self.profile:
            x = chart.left() + (
                (distance - first_distance) / distance_range
            ) * chart.width()
            y = chart.bottom() - (
                (elevation - minimum) / elevation_range
            ) * chart.height()
            plotted_points.append(QPointF(x, y))

        line_path = QPainterPath(plotted_points[0])
        for point in plotted_points[1:]:
            line_path.lineTo(point)

        fill_path = QPainterPath(line_path)
        fill_path.lineTo(plotted_points[-1].x(), chart.bottom())
        fill_path.lineTo(plotted_points[0].x(), chart.bottom())
        fill_path.closeSubpath()

        painter.fillPath(fill_path, QColor(colors["chart_fill"]))
        painter.setPen(QPen(QColor(colors["chart_line"]), 2.5))
        painter.drawPath(line_path)

        if self.selected_distance is not None:
            selected_profile_point = min(
                self.profile,
                key=lambda point: abs(point[0] - self.selected_distance),
            )
            selected_x = chart.left() + (
                (selected_profile_point[0] - first_distance) / distance_range
            ) * chart.width()
            selected_y = chart.bottom() - (
                (selected_profile_point[1] - minimum) / elevation_range
            ) * chart.height()
            painter.setPen(QPen(QColor("#d97931"), 1.5))
            painter.drawLine(
                QPointF(selected_x, chart.top()),
                QPointF(selected_x, chart.bottom()),
            )
            painter.setBrush(QColor("#d97931"))
            painter.drawEllipse(QPointF(selected_x, selected_y), 5, 5)

        painter.setPen(QColor(colors["muted"]))
        painter.drawText(
            4,
            chart.top() - 7,
            45,
            18,
            Qt.AlignmentFlag.AlignRight,
            f"{maximum:.0f} m",
        )
        painter.drawText(
            4,
            chart.bottom() - 9,
            45,
            18,
            Qt.AlignmentFlag.AlignRight,
            f"{minimum:.0f} m",
        )
        painter.drawText(
            chart.left(),
            chart.bottom() + 8,
            70,
            20,
            Qt.AlignmentFlag.AlignLeft,
            "Start",
        )
        painter.drawText(
            chart.right() - 100,
            chart.bottom() + 8,
            100,
            20,
            Qt.AlignmentFlag.AlignRight,
            _format_distance(self.total_distance_metres),
        )


def _format_distance(metres: float) -> str:
    if metres >= 1000:
        return f"{metres / 1000:.1f} km"
    return f"{metres:.0f} m"
