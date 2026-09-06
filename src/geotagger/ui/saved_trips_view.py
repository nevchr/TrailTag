from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..trip_store import SavedTrip, TripStore, TripStoreError
from .elevation_profile import ElevationProfile
from .map_view import MapView
from .photo_gallery import PhotoGallery


class SavedTripsView(QWidget):
    open_trip_requested = Signal(object)
    status_message = Signal(str, str)
    trip_changed = Signal(object)
    trip_deleted = Signal(str)

    def __init__(self, trip_store: TripStore):
        super().__init__()

        self.trip_store = trip_store
        self.trips_by_id: dict[str, SavedTrip] = {}
        self.current_trip: SavedTrip | None = None

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        library_panel = QFrame()
        library_panel.setObjectName("tripLibraryPanel")
        library_panel.setMinimumWidth(235)
        library_panel.setMaximumWidth(310)

        library_layout = QVBoxLayout(library_panel)
        library_layout.setContentsMargins(14, 14, 14, 14)
        library_layout.setSpacing(8)

        library_title = QLabel("Your trips")
        library_title.setObjectName("tripPanelTitle")
        library_help = QLabel("Saved on this computer")
        library_help.setObjectName("helperText")

        self.trip_list = QListWidget()
        self.trip_list.setObjectName("tripList")
        self.trip_list.setSpacing(4)
        self.trip_list.currentItemChanged.connect(self._show_selected_trip)

        library_layout.addWidget(library_title)
        library_layout.addWidget(library_help)
        library_layout.addWidget(self.trip_list, 1)

        self.empty_label = QLabel(
            "No saved trips yet.\n\nPreview a route, then choose Save trip."
        )
        self.empty_label.setObjectName("savedTripEmpty")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setWordWrap(True)

        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(10)

        self.trip_title = QLabel()
        self.trip_title.setObjectName("savedTripTitle")
        self.trip_title.setWordWrap(True)

        self.saved_date_label = QLabel()
        self.saved_date_label.setObjectName("helperText")

        title_text_layout = QVBoxLayout()
        title_text_layout.setSpacing(1)
        title_text_layout.addWidget(self.trip_title)
        title_text_layout.addWidget(self.saved_date_label)

        self.open_button = QPushButton("Open for editing")
        self.rename_button = QPushButton("Rename")
        self.reconnect_button = QPushButton("Reconnect photos")
        self.delete_button = QPushButton("Delete")

        for button in (
            self.open_button,
            self.rename_button,
            self.reconnect_button,
        ):
            button.setObjectName("compactAction")
        self.delete_button.setObjectName("dangerAction")

        self.open_button.clicked.connect(self._request_open_trip)
        self.rename_button.clicked.connect(self._rename_trip)
        self.reconnect_button.clicked.connect(self._reconnect_photos)
        self.delete_button.clicked.connect(self._delete_trip)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(6)
        action_layout.addWidget(self.open_button)
        action_layout.addWidget(self.rename_button)
        action_layout.addWidget(self.reconnect_button)
        action_layout.addWidget(self.delete_button)

        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)
        title_layout.addLayout(title_text_layout, 1)
        title_layout.addLayout(action_layout)
        details_layout.addLayout(title_layout)

        self.file_status_label = QLabel()
        self.file_status_label.setObjectName("sourceStatus")
        self.file_status_label.setWordWrap(True)
        details_layout.addWidget(self.file_status_label)

        summary_grid = QGridLayout()
        summary_grid.setHorizontalSpacing(8)
        summary_grid.setVerticalSpacing(8)

        self.distance_value = self._add_stat(
            summary_grid, 0, 0, "Distance"
        )
        self.duration_value = self._add_stat(
            summary_grid, 0, 1, "Time"
        )
        self.photos_value = self._add_stat(
            summary_grid, 0, 2, "Matched photos"
        )
        self.elevation_gain_value = self._add_stat(
            summary_grid, 1, 0, "Elevation gain"
        )
        self.average_speed_value = self._add_stat(
            summary_grid, 1, 1, "Average speed"
        )
        self.points_value = self._add_stat(
            summary_grid, 1, 2, "Route points"
        )
        summary_grid.setColumnStretch(0, 1)
        summary_grid.setColumnStretch(1, 1)
        summary_grid.setColumnStretch(2, 1)
        details_layout.addLayout(summary_grid)

        route_details = QFrame()
        route_details.setObjectName("tripDetailsPanel")
        route_grid = QGridLayout(route_details)
        route_grid.setContentsMargins(12, 9, 12, 9)
        route_grid.setHorizontalSpacing(14)
        route_grid.setVerticalSpacing(5)
        route_grid.setColumnStretch(1, 1)
        route_grid.setColumnStretch(3, 1)

        self.route_time_value = QLabel()
        self.start_location_value = QLabel()
        self.end_location_value = QLabel()
        self.settings_value = QLabel()

        detail_rows = [
            ("Route time", self.route_time_value, "Photo settings", self.settings_value),
            (
                "Start location",
                self.start_location_value,
                "End location",
                self.end_location_value,
            ),
        ]

        for row, (left_title, left_value, right_title, right_value) in enumerate(
            detail_rows
        ):
            left_label = QLabel(left_title)
            left_label.setObjectName("tripDetailLabel")
            right_label = QLabel(right_title)
            right_label.setObjectName("tripDetailLabel")

            left_value.setObjectName("tripDetailValue")
            right_value.setObjectName("tripDetailValue")
            left_value.setWordWrap(True)
            right_value.setWordWrap(True)

            route_grid.addWidget(left_label, row, 0)
            route_grid.addWidget(left_value, row, 1)
            route_grid.addWidget(right_label, row, 2)
            route_grid.addWidget(right_value, row, 3)

        details_layout.addWidget(route_details)

        self.map_view = MapView()
        self.elevation_profile = ElevationProfile()
        self.photo_gallery = PhotoGallery()
        self.photo_gallery.photo_selected.connect(self._gallery_photo_selected)
        self.map_view.photo_selected.connect(self._map_photo_selected)

        gallery_panel = QFrame()
        gallery_panel.setObjectName("tripGalleryPanel")
        gallery_panel.setMinimumWidth(180)
        gallery_panel.setMaximumWidth(215)
        gallery_layout = QVBoxLayout(gallery_panel)
        gallery_layout.setContentsMargins(8, 9, 8, 8)
        gallery_layout.setSpacing(5)
        gallery_title = QLabel("Trip gallery")
        gallery_title.setObjectName("tripGalleryTitle")
        gallery_help = QLabel("Select a photo to find it on the route")
        gallery_help.setObjectName("tripGalleryHelp")
        gallery_help.setWordWrap(True)
        gallery_layout.addWidget(gallery_title)
        gallery_layout.addWidget(gallery_help)
        gallery_layout.addWidget(self.photo_gallery, 1)

        self.visual_tabs = QTabWidget()
        self.visual_tabs.setObjectName("tripVisualTabs")
        self.visual_tabs.addTab(self.map_view, "Route map")
        self.visual_tabs.addTab(self.elevation_profile, "Elevation profile")
        self.visual_tabs.setMinimumHeight(210)

        visual_layout = QHBoxLayout()
        visual_layout.setSpacing(9)
        visual_layout.addWidget(gallery_panel)
        visual_layout.addWidget(self.visual_tabs, 1)
        details_layout.addLayout(visual_layout, 1)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.empty_label, 1)
        content_layout.addWidget(self.details_widget, 1)

        layout.addWidget(library_panel)
        layout.addWidget(content, 1)

    def _add_stat(
        self,
        layout: QGridLayout,
        row: int,
        column: int,
        title: str,
    ) -> QLabel:
        card = QFrame()
        card.setObjectName("tripStatCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(1)

        value = QLabel("—")
        value.setObjectName("tripStatValue")
        label = QLabel(title)
        label.setObjectName("tripStatLabel")

        card_layout.addWidget(value)
        card_layout.addWidget(label)
        layout.addWidget(card, row, column)
        return value

    def refresh(self, select_trip_id: str | None = None) -> bool:
        try:
            trips = self.trip_store.load_trips()
        except TripStoreError as error:
            self.trips_by_id = {}
            self.current_trip = None
            self.trip_list.clear()
            self.empty_label.setText(str(error))
            self.empty_label.show()
            self.details_widget.hide()
            self.map_view.show_empty_map("Saved trips could not be loaded.")
            self.elevation_profile.set_track_points([])
            self.photo_gallery.set_results([])
            return False

        self.trips_by_id = {trip.trip_id: trip for trip in trips}
        self.trip_list.blockSignals(True)
        self.trip_list.clear()

        selected_row = 0
        for row, trip in enumerate(trips):
            item = QListWidgetItem(
                f"{trip.name}\n{_format_date(trip.start_time or trip.saved_at)}"
                f"  •  {_format_distance(trip.distance_metres)}"
            )
            item.setData(Qt.ItemDataRole.UserRole, trip.trip_id)
            item.setSizeHint(QSize(0, 58))
            self.trip_list.addItem(item)
            if trip.trip_id == select_trip_id:
                selected_row = row

        self.trip_list.blockSignals(False)

        if not trips:
            self.current_trip = None
            self.empty_label.setText(
                "No saved trips yet.\n\nPreview a route, then choose Save trip."
            )
            self.empty_label.show()
            self.details_widget.hide()
            self.map_view.show_empty_map("Select a saved trip to view its route.")
            self.elevation_profile.set_track_points([])
            self.photo_gallery.set_results([])
            return True

        self.trip_list.setCurrentRow(selected_row)
        self._display_trip(trips[selected_row])
        return True

    def _show_selected_trip(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        del previous
        if current is None:
            return

        trip_id = current.data(Qt.ItemDataRole.UserRole)
        trip = self.trips_by_id.get(trip_id)
        if trip is not None:
            self._display_trip(trip)

    def _display_trip(self, trip: SavedTrip) -> None:
        self.current_trip = trip
        self.empty_label.hide()
        self.details_widget.show()

        self.trip_title.setText(trip.name)
        self.saved_date_label.setText(
            f"Saved {_format_saved_date(trip.saved_at)}"
        )
        self.distance_value.setText(_format_distance(trip.distance_metres))
        self.duration_value.setText(_format_duration(trip.duration))
        self.photos_value.setText(
            f"{trip.matched_photo_count} / {len(trip.preview_results)}"
        )
        self.elevation_gain_value.setText(
            _format_elevation_gain(trip.elevation_gain_metres)
        )
        self.average_speed_value.setText(
            _format_average_speed(trip.average_speed_kmh)
        )
        self.points_value.setText(f"{len(trip.track_points):,}")
        self.route_time_value.setText(_format_time_range(trip))
        self.start_location_value.setText(_format_endpoint(trip, first=True))
        self.end_location_value.setText(_format_endpoint(trip, first=False))
        self.settings_value.setText(
            f"{trip.timezone_name}  •  {_format_offset(trip.time_offset_seconds)}"
            f"  •  {trip.max_gap_minutes} min gap"
        )
        status_text, status_kind = _source_status(trip)
        self.file_status_label.setText(status_text)
        self.file_status_label.setProperty("kind", status_kind)
        self.file_status_label.style().unpolish(self.file_status_label)
        self.file_status_label.style().polish(self.file_status_label)
        self.reconnect_button.setEnabled(bool(trip.preview_results))
        self.map_view.set_results(trip.track_points, trip.preview_results)
        self.elevation_profile.set_track_points(trip.track_points)
        self.photo_gallery.set_results(trip.preview_results)

    def _gallery_photo_selected(self, photo_index: int) -> None:
        if self.current_trip is None:
            return
        if not 0 <= photo_index < len(self.current_trip.preview_results):
            return

        result = self.current_trip.preview_results[photo_index]
        self.elevation_profile.focus_location(
            result.latitude,
            result.longitude,
        )
        if result.matched:
            self.map_view.focus_photo(photo_index)

    def _map_photo_selected(self, photo_index: int) -> None:
        if self.current_trip is None:
            return
        if not 0 <= photo_index < len(self.current_trip.preview_results):
            return

        result = self.current_trip.preview_results[photo_index]
        self.photo_gallery.select_photo(photo_index)
        self.elevation_profile.focus_location(
            result.latitude,
            result.longitude,
        )

    def _selected_trip(self) -> SavedTrip | None:
        current = self.trip_list.currentItem()
        if current is None:
            return None
        trip_id = current.data(Qt.ItemDataRole.UserRole)
        return self.trips_by_id.get(trip_id)

    def _request_open_trip(self) -> None:
        trip = self._selected_trip()
        if trip is not None:
            self.open_trip_requested.emit(trip)

    def _rename_trip(self) -> None:
        trip = self._selected_trip()
        if trip is None:
            return

        name, accepted = QInputDialog.getText(
            self,
            "Rename Trip",
            "Trip name:",
            text=trip.name,
        )
        name = name.strip()
        if not accepted:
            return
        if not name:
            QMessageBox.warning(
                self,
                "Trip Name Required",
                "Please enter a name for this trip.",
            )
            return

        previous_name = trip.name
        trip.name = name
        try:
            self.trip_store.save_trip(trip)
        except TripStoreError as error:
            trip.name = previous_name
            QMessageBox.critical(self, "Rename Failed", str(error))
            return

        self.refresh(select_trip_id=trip.trip_id)
        self.trip_changed.emit(trip)
        self.status_message.emit(f'Changed the trip name to “{name}”.', "success")

    def _delete_trip(self) -> None:
        trip = self._selected_trip()
        if trip is None:
            return

        answer = QMessageBox.question(
            self,
            "Delete Saved Trip",
            (
                f'Delete “{trip.name}” from TrailTag?\n\n'
                "Your GPX and photo files will not be deleted."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.trip_store.delete_trip(trip.trip_id)
        except TripStoreError as error:
            QMessageBox.critical(self, "Delete Failed", str(error))
            return

        self.refresh()
        self.trip_deleted.emit(trip.trip_id)
        self.status_message.emit(
            f'“{trip.name}” was removed from Saved trips.',
            "success",
        )

    def _reconnect_photos(self) -> None:
        trip = self._selected_trip()
        if trip is None or not trip.preview_results:
            return

        folder = QFileDialog.getExistingDirectory(
            self,
            "Reconnect Original Photos",
            str(trip.photo_folder or ""),
        )
        if not folder:
            return

        new_folder = Path(folder)
        replacements = [
            new_folder / result.source_path.name
            for result in trip.preview_results
        ]
        found_count = sum(path.is_file() for path in replacements)

        if found_count == 0:
            QMessageBox.warning(
                self,
                "Photos Not Found",
                "TrailTag could not find any of this trip's photos in that folder.",
            )
            return

        previous_folder = trip.photo_folder
        previous_paths = [
            result.source_path for result in trip.preview_results
        ]
        for result, replacement in zip(trip.preview_results, replacements):
            result.source_path = replacement
        trip.photo_folder = new_folder

        try:
            self.trip_store.save_trip(trip)
        except TripStoreError as error:
            trip.photo_folder = previous_folder
            for result, previous_path in zip(
                trip.preview_results,
                previous_paths,
            ):
                result.source_path = previous_path
            QMessageBox.critical(self, "Reconnect Failed", str(error))
            return

        self.refresh(select_trip_id=trip.trip_id)
        self.trip_changed.emit(trip)
        kind = "success" if found_count == len(replacements) else "warning"
        self.status_message.emit(
            f"Reconnected {found_count} of {len(replacements)} trip photos.",
            kind,
        )


def _format_distance(metres: float) -> str:
    if metres >= 1000:
        return f"{metres / 1000:.1f} km"
    return f"{metres:.0f} m"


def _format_duration(duration: timedelta) -> str:
    total_seconds = max(0, int(duration.total_seconds()))
    days, remainder = divmod(total_seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)

    if days:
        return f"{days} d {hours} h"
    if hours:
        return f"{hours} h {minutes} min"
    if minutes:
        return f"{minutes} min"
    return f"{seconds} sec"


def _format_elevation_gain(metres: float | None) -> str:
    if metres is None:
        return "Not available"
    return f"{metres:.0f} m"


def _format_average_speed(speed_kmh: float | None) -> str:
    if speed_kmh is None:
        return "Not available"
    return f"{speed_kmh:.1f} km/h"


def _format_date(value: datetime) -> str:
    return f"{value.strftime('%b')} {value.day}, {value.year}"


def _format_saved_date(value: datetime) -> str:
    local_value = value.astimezone() if value.tzinfo is not None else value
    return (
        f"{_format_date(local_value)} at "
        f"{local_value.strftime('%I:%M %p').lstrip('0')}"
    )


def _format_time_range(trip: SavedTrip) -> str:
    if trip.start_time is None or trip.end_time is None:
        return "Not available"

    start = trip.start_time
    end = trip.end_time
    start_time = start.strftime("%I:%M %p").lstrip("0")
    end_time = end.strftime("%I:%M %p").lstrip("0")

    if start.date() == end.date():
        return f"{_format_date(start)}  •  {start_time}–{end_time}"
    return f"{_format_date(start)} {start_time} – {_format_date(end)} {end_time}"


def _format_endpoint(trip: SavedTrip, *, first: bool) -> str:
    if not trip.track_points:
        return "Not available"
    point = trip.track_points[0 if first else -1]
    return f"{point.latitude:.5f}, {point.longitude:.5f}"


def _format_offset(offset_seconds: int) -> str:
    if offset_seconds == 0:
        return "no clock offset"

    sign = "+" if offset_seconds > 0 else "−"
    remaining = abs(offset_seconds)
    hours, remaining = divmod(remaining, 3_600)
    minutes, seconds = divmod(remaining, 60)
    pieces = []
    if hours:
        pieces.append(f"{hours}h")
    if minutes:
        pieces.append(f"{minutes}m")
    if seconds:
        pieces.append(f"{seconds}s")
    return f"{sign}{' '.join(pieces)} offset"


def _source_status(trip: SavedTrip) -> tuple[str, str]:
    notices = []

    if trip.gpx_path is not None and not trip.gpx_path.is_file():
        notices.append("The original GPX file has moved")

    missing_photos = sum(
        not result.source_path.is_file()
        for result in trip.preview_results
    )
    if missing_photos:
        noun = "photo is" if missing_photos == 1 else "photos are"
        notices.append(f"{missing_photos} original {noun} unavailable")

    if notices:
        return (
            ". ".join(notices)
            + ". The saved route is still available; reconnect photos when needed.",
            "warning",
        )
    return "Original source files are connected.", "success"
