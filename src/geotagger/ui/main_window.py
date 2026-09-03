from datetime import timedelta
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..gpx_parser import load_gpx
from ..preview import preview_folder
from ..processor import process_preview_results
from .map_view import MapView
from .preview_table import PreviewTable


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GPX Photo Geotagger")
        self.resize(1200, 800)

        self.gpx_path: Path | None = None
        self.photo_folder: Path | None = None
        self.output_folder: Path | None = None

        self.track_points = []
        self.preview_results = []

        self.build_ui()

    def build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        main_layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        main_layout.setSpacing(16)

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        title = QLabel(
            "GPX Photo Geotagger"
        )

        title.setStyleSheet(
            "font-size: 24px; font-weight: 600;"
        )

        description = QLabel(
            "Match photo capture times to a GPX track and "
            "preview their calculated GPS locations."
        )

        main_layout.addWidget(title)
        main_layout.addWidget(description)

        # -------------------------------------------------
        # GPX file
        # -------------------------------------------------

        gpx_layout = QHBoxLayout()

        self.gpx_field = QLineEdit()

        self.gpx_field.setPlaceholderText(
            "No GPX file selected"
        )

        self.gpx_field.setReadOnly(True)

        gpx_button = QPushButton(
            "Browse"
        )

        gpx_button.clicked.connect(
            self.select_gpx_file
        )

        gpx_layout.addWidget(
            self.gpx_field
        )

        gpx_layout.addWidget(
            gpx_button
        )

        # -------------------------------------------------
        # Photo folder
        # -------------------------------------------------

        photo_layout = QHBoxLayout()

        self.photo_field = QLineEdit()

        self.photo_field.setPlaceholderText(
            "No photo folder selected"
        )

        self.photo_field.setReadOnly(True)

        photo_button = QPushButton(
            "Browse"
        )

        photo_button.clicked.connect(
            self.select_photo_folder
        )

        photo_layout.addWidget(
            self.photo_field
        )

        photo_layout.addWidget(
            photo_button
        )

        # -------------------------------------------------
        # Output folder
        # -------------------------------------------------

        output_layout = QHBoxLayout()

        self.output_field = QLineEdit()

        self.output_field.setPlaceholderText(
            "No output folder selected"
        )

        self.output_field.setReadOnly(True)

        output_button = QPushButton(
            "Browse"
        )

        output_button.clicked.connect(
            self.select_output_folder
        )

        output_layout.addWidget(
            self.output_field
        )

        output_layout.addWidget(
            output_button
        )

        # -------------------------------------------------
        # Timezone
        # -------------------------------------------------

        self.timezone_combo = QComboBox()

        self.timezone_combo.setEditable(
            True
        )

        self.timezone_combo.addItems(
            [
                "America/Toronto",
                "America/Vancouver",
                "America/Edmonton",
                "America/Winnipeg",
                "America/Halifax",
                "America/St_Johns",
                "UTC",
            ]
        )

        self.timezone_combo.setCurrentText(
            "America/Toronto"
        )

        # -------------------------------------------------
        # Time offset
        # -------------------------------------------------

        offset_layout = QHBoxLayout()

        self.offset_hours = QSpinBox()

        self.offset_hours.setRange(
            -23,
            23,
        )

        self.offset_hours.setSuffix(
            " h"
        )

        self.offset_minutes = QSpinBox()

        self.offset_minutes.setRange(
            -59,
            59,
        )

        self.offset_minutes.setSuffix(
            " min"
        )

        self.offset_seconds = QSpinBox()

        self.offset_seconds.setRange(
            -59,
            59,
        )

        self.offset_seconds.setSuffix(
            " sec"
        )

        offset_layout.addWidget(
            self.offset_hours
        )

        offset_layout.addWidget(
            self.offset_minutes
        )

        offset_layout.addWidget(
            self.offset_seconds
        )

        # -------------------------------------------------
        # Maximum track gap
        # -------------------------------------------------

        self.max_gap = QSpinBox()

        self.max_gap.setRange(
            1,
            120,
        )

        self.max_gap.setValue(
            5
        )

        self.max_gap.setSuffix(
            " minutes"
        )

        # -------------------------------------------------
        # Form
        # -------------------------------------------------

        form_layout = QFormLayout()

        form_layout.addRow(
            "GPX Track:",
            gpx_layout,
        )

        form_layout.addRow(
            "Photo Folder:",
            photo_layout,
        )

        form_layout.addRow(
            "Output Folder:",
            output_layout,
        )

        form_layout.addRow(
            "Photo Timezone:",
            self.timezone_combo,
        )

        form_layout.addRow(
            "Time Offset:",
            offset_layout,
        )

        form_layout.addRow(
            "Maximum Track Gap:",
            self.max_gap,
        )

        main_layout.addLayout(
            form_layout
        )

        # -------------------------------------------------
        # Preview tabs
        # -------------------------------------------------

        self.preview_tabs = QTabWidget()

        self.preview_table = PreviewTable()

        self.map_view = MapView()

        self.preview_tabs.addTab(
            self.preview_table,
            "Photos",
        )

        self.preview_tabs.addTab(
            self.map_view,
            "Map",
        )

        self.preview_tabs.setMinimumHeight(
            350
        )

        main_layout.addWidget(
            self.preview_tabs
        )

        # -------------------------------------------------
        # Status
        # -------------------------------------------------

        self.status_label = QLabel(
            "Select a GPX track and photo folder to begin."
        )

        main_layout.addWidget(
            self.status_label
        )

        # -------------------------------------------------
        # Preview button
        # -------------------------------------------------

        self.preview_button = QPushButton(
            "Preview Matches"
        )

        self.preview_button.setMinimumHeight(
            40
        )

        self.preview_button.clicked.connect(
            self.preview_matches
        )

        main_layout.addWidget(
            self.preview_button
        )

        # -------------------------------------------------
        # Process button
        # -------------------------------------------------

        self.process_button = QPushButton(
            "Create Geotagged Photos"
        )

        self.process_button.setMinimumHeight(
            40
        )

        self.process_button.setEnabled(
            False
        )

        self.process_button.clicked.connect(
            self.process_photos
        )

        main_layout.addWidget(
            self.process_button
        )

    # -----------------------------------------------------
    # File selection
    # -----------------------------------------------------

    def select_gpx_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select GPX Track",
            "",
            "GPX Files (*.gpx)",
        )

        if not file_path:
            return

        self.gpx_path = Path(
            file_path
        )

        self.gpx_field.setText(
            file_path
        )

        self.clear_preview()

    def select_photo_folder(self):
        folder_path = (
            QFileDialog.getExistingDirectory(
                self,
                "Select Photo Folder",
            )
        )

        if not folder_path:
            return

        self.photo_folder = Path(
            folder_path
        )

        self.photo_field.setText(
            folder_path
        )

        self.clear_preview()

    def select_output_folder(self):
        folder_path = (
            QFileDialog.getExistingDirectory(
                self,
                "Select Output Folder",
            )
        )

        if not folder_path:
            return

        self.output_folder = Path(
            folder_path
        )

        self.output_field.setText(
            folder_path
        )

    # -----------------------------------------------------
    # Settings
    # -----------------------------------------------------

    def get_time_offset(self) -> timedelta:
        return timedelta(
            hours=self.offset_hours.value(),
            minutes=self.offset_minutes.value(),
            seconds=self.offset_seconds.value(),
        )

    # -----------------------------------------------------
    # Preview state
    # -----------------------------------------------------

    def clear_preview(self):
        self.track_points = []
        self.preview_results = []

        self.preview_table.setRowCount(
            0
        )

        self.map_view.show_empty_map()

        self.process_button.setEnabled(
            False
        )

        self.status_label.setText(
            "Preview required."
        )

    # -----------------------------------------------------
    # Preview
    # -----------------------------------------------------

    def preview_matches(self):
        if self.gpx_path is None:
            QMessageBox.warning(
                self,
                "Missing GPX Track",
                "Please select a GPX file.",
            )

            return

        if self.photo_folder is None:
            QMessageBox.warning(
                self,
                "Missing Photo Folder",
                "Please select a photo folder.",
            )

            return

        timezone_name = (
            self.timezone_combo
            .currentText()
            .strip()
        )

        if not timezone_name:
            QMessageBox.warning(
                self,
                "Missing Timezone",
                "Please enter a photo timezone.",
            )

            return

        self.preview_button.setEnabled(
            False
        )

        self.process_button.setEnabled(
            False
        )

        self.status_label.setText(
            "Generating preview..."
        )

        try:
            self.track_points = load_gpx(
                self.gpx_path
            )

            if not self.track_points:
                QMessageBox.warning(
                    self,
                    "Invalid GPX",
                    (
                        "The GPX file contains no "
                        "timestamped track points."
                    ),
                )

                self.preview_button.setEnabled(
                    True
                )

                return

            self.preview_results = (
                preview_folder(
                    photo_folder=self.photo_folder,
                    track_points=self.track_points,
                    timezone_name=timezone_name,
                    time_offset=self.get_time_offset(),
                    max_interpolation_gap=timedelta(
                        minutes=self.max_gap.value()
                    ),
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Preview Failed",
                str(error),
            )

            self.preview_button.setEnabled(
                True
            )

            return

        # Table
        self.preview_table.set_results(
            self.preview_results
        )

        # Map
        self.map_view.set_results(
            track_points=self.track_points,
            preview_results=self.preview_results,
        )

        matched = sum(
            result.matched
            for result in self.preview_results
        )

        unmatched = (
            len(self.preview_results)
            - matched
        )

        self.status_label.setText(
            f"{len(self.preview_results)} photos  •  "
            f"{matched} matched  •  "
            f"{unmatched} unmatched"
        )

        self.process_button.setEnabled(
            matched > 0
        )

        self.preview_button.setEnabled(
            True
        )

    # -----------------------------------------------------
    # Processing
    # -----------------------------------------------------

    def process_photos(self):
        if not self.preview_results:
            QMessageBox.warning(
                self,
                "No Preview",
                "Preview the photos before processing.",
            )

            return

        if self.output_folder is None:
            QMessageBox.warning(
                self,
                "Missing Output Folder",
                "Please select an output folder.",
            )

            return

        self.process_button.setEnabled(
            False
        )

        self.preview_button.setEnabled(
            False
        )

        self.status_label.setText(
            "Creating geotagged photos..."
        )

        try:
            results = process_preview_results(
                preview_results=self.preview_results,
                output_folder=self.output_folder,
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Processing Failed",
                str(error),
            )

            self.process_button.setEnabled(
                True
            )

            self.preview_button.setEnabled(
                True
            )

            return

        successful = sum(
            result.success
            for result in results
        )

        failed = (
            len(results)
            - successful
        )

        self.status_label.setText(
            f"{len(results)} processed  •  "
            f"{successful} geotagged  •  "
            f"{failed} failed"
        )

        QMessageBox.information(
            self,
            "Processing Complete",
            (
                f"{len(results)} photos processed\n\n"
                f"{successful} successfully geotagged\n"
                f"{failed} failed"
            ),
        )

        self.process_button.setEnabled(
            True
        )

        self.preview_button.setEnabled(
            True
        )