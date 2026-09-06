from datetime import timedelta
from pathlib import Path

from PySide6.QtCore import QSettings, QSignalBlocker, QThread, QTimer, Qt
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..processor import ProcessResult
from ..trip_store import SavedTrip, TripStore, TripStoreError, create_saved_trip
from ..version import __version__, resource_path
from ..workers import PreviewBatch, PreviewWorker, ProcessingWorker
from .map_view import MapView
from .preview_table import PreviewTable
from .saved_trips_view import SavedTripsView
from .theme import apply_theme, themed_stylesheet


APP_STYLESHEET = """
QMainWindow, QWidget#appRoot {
    background: #f3f7f5;
    color: #18352b;
    font-family: "Segoe UI";
    font-size: 10pt;
}

QFrame#card {
    background: #ffffff;
    border: 1px solid #dce7e1;
    border-radius: 12px;
}

QFrame#operationPanel {
    padding: 5px 8px;
    border: 1px solid #cfe0d7;
    border-radius: 8px;
    background: #ffffff;
}

QLabel#operationLabel {
    color: #40574d;
    font-size: 9pt;
    font-weight: 600;
}

QProgressBar {
    min-height: 16px;
    border: 1px solid #cfddd6;
    border-radius: 7px;
    background: #edf2ef;
    color: #24483a;
    text-align: center;
    font-size: 8pt;
}

QProgressBar::chunk {
    border-radius: 6px;
    background: #2b8a67;
}

QLabel#brandTitle {
    color: #143d30;
    font-size: 26px;
    font-weight: 700;
}

QLabel#brandSubtitle, QLabel#helperText, QLabel#safetyNote {
    color: #687970;
}

QLabel#localBadge {
    padding: 7px 11px;
    border: 1px solid #c9e7d8;
    border-radius: 13px;
    background: #eaf7f0;
    color: #176b4d;
    font-size: 9pt;
    font-weight: 600;
}

QLabel#stepLabel {
    color: #18704f;
    font-size: 9pt;
    font-weight: 700;
}

QLabel#sectionTitle {
    color: #18352b;
    font-size: 14pt;
    font-weight: 650;
}

QLabel#fieldLabel {
    color: #40574d;
    font-size: 9pt;
    font-weight: 600;
}

QLineEdit, QComboBox, QSpinBox {
    min-height: 34px;
    padding: 0 10px;
    border: 1px solid #cfdcd5;
    border-radius: 7px;
    background: #fbfdfc;
    color: #29473b;
    selection-background-color: #2b8a67;
    selection-color: #ffffff;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #27815f;
    background: #ffffff;
}

QLineEdit:read-only {
    color: #40574d;
}

QPushButton {
    min-height: 34px;
    padding: 0 16px;
    border-radius: 7px;
    font-weight: 600;
}

QPushButton#browseButton, QPushButton#secondaryAction {
    border: 1px solid #b9cbc2;
    background: #ffffff;
    color: #24483a;
}

QPushButton#browseButton:hover, QPushButton#secondaryAction:hover {
    border-color: #27815f;
    background: #f0f8f4;
}

QPushButton#compactAction, QPushButton#dangerAction {
    min-height: 28px;
    padding: 0 9px;
    background: #ffffff;
}

QPushButton#compactAction {
    border: 1px solid #b9cbc2;
    color: #24483a;
}

QPushButton#compactAction:hover {
    border-color: #27815f;
    background: #f0f8f4;
}

QPushButton#dangerAction {
    border: 1px solid #e3c4c1;
    color: #9a3d32;
}

QPushButton#dangerAction:hover {
    border-color: #c56a61;
    background: #fff3f1;
}

QPushButton#primaryAction {
    border: 1px solid #176b4d;
    background: #176b4d;
    color: #ffffff;
}

QPushButton#primaryAction:hover {
    border-color: #125a40;
    background: #125a40;
}

QPushButton#primaryAction:disabled,
QPushButton#secondaryAction:disabled {
    border-color: #d7dfdb;
    background: #e8edeb;
    color: #94a19b;
}

QLabel#statusPill {
    padding: 7px 11px;
    border-radius: 13px;
    font-size: 9pt;
    font-weight: 600;
}

QLabel#statusPill[kind="neutral"] {
    background: #edf1ef;
    color: #52645b;
}

QLabel#statusPill[kind="busy"] {
    background: #e8f1fb;
    color: #245c91;
}

QLabel#statusPill[kind="success"] {
    background: #e6f6ed;
    color: #176b4d;
}

QLabel#statusPill[kind="warning"] {
    background: #fff3d6;
    color: #805500;
}

QLabel#statusPill[kind="error"] {
    background: #fdeaea;
    color: #a03333;
}

QTabWidget::pane {
    border: 1px solid #dce7e1;
    border-radius: 8px;
    background: #ffffff;
    top: -1px;
}

QTabBar::tab {
    min-width: 120px;
    padding: 9px 16px;
    border: 1px solid transparent;
    border-bottom: 2px solid transparent;
    background: transparent;
    color: #65766d;
    font-weight: 600;
}

QTabBar::tab:selected {
    border-bottom-color: #1b7a57;
    color: #176b4d;
}

QTabBar::tab:hover:!selected {
    color: #24483a;
}

QTableWidget {
    color: #18352b;
    border: 0;
    background: #ffffff;
    alternate-background-color: #f7faf8;
    gridline-color: #edf2ef;
    selection-background-color: #dff1e8;
    selection-color: #18352b;
}

QHeaderView::section {
    padding: 9px 8px;
    border: 0;
    border-bottom: 1px solid #dce7e1;
    background: #f1f6f3;
    color: #40574d;
    font-weight: 650;
}

QFrame#tripLibraryPanel, QFrame#tripDetailsPanel, QFrame#tripStatCard,
QFrame#tripGalleryPanel {
    border: 1px solid #dce7e1;
    border-radius: 8px;
    background: #f8fbf9;
}

QLabel#tripPanelTitle, QLabel#savedTripTitle {
    color: #18352b;
    font-size: 13pt;
    font-weight: 650;
}

QLabel#tripGalleryTitle {
    color: #18352b;
    font-size: 10pt;
    font-weight: 650;
}

QLabel#tripGalleryHelp {
    color: #687970;
    font-size: 8pt;
}

QListWidget#photoGallery {
    color: #18352b;
    selection-color: #18352b;
    border: 0;
    background: transparent;
    outline: 0;
}

QListWidget#photoGallery::item {
    padding: 4px;
    border: 1px solid transparent;
    border-radius: 7px;
}

QListWidget#photoGallery::item:selected {
    border-color: #79bd9f;
    background: #e6f4ec;
}

QListWidget#tripList {
    border: 0;
    background: transparent;
    outline: 0;
}

QListWidget#tripList::item {
    margin: 1px 0;
    padding: 7px 9px;
    border: 1px solid transparent;
    border-radius: 7px;
    color: #40574d;
}

QListWidget#tripList::item:selected {
    border-color: #b9dfcc;
    background: #e6f4ec;
    color: #175b43;
}

QListWidget#tripList::item:hover:!selected {
    background: #eef5f1;
}

QLabel#savedTripEmpty {
    padding: 24px;
    color: #687970;
    font-size: 11pt;
}

QLabel#tripStatValue {
    color: #176b4d;
    font-size: 13pt;
    font-weight: 700;
}

QLabel#tripStatLabel, QLabel#tripDetailLabel {
    color: #687970;
    font-size: 8.5pt;
    font-weight: 600;
}

QLabel#tripDetailValue {
    color: #29473b;
    font-size: 9pt;
}

QLabel#sourceStatus {
    padding: 6px 9px;
    border-radius: 6px;
    font-size: 8.5pt;
}

QLabel#sourceStatus[kind="success"] {
    background: #e9f6ef;
    color: #176b4d;
}

QLabel#sourceStatus[kind="warning"] {
    background: #fff3d6;
    color: #805500;
}
"""


class MainWindow(QMainWindow):
    def __init__(
        self,
        trip_store: TripStore | None = None,
        settings: QSettings | None = None,
    ):
        super().__init__()
        self.setWindowIcon(QIcon(str(resource_path("packaging", "trailtag.ico"))))

        self.setWindowTitle("TrailTag")
        self.setAccessibleName("TrailTag GPX photo geotagger")
        self.resize(1240, 820)
        self.setMinimumSize(980, 700)

        self.gpx_path: Path | None = None
        self.photo_folder: Path | None = None
        self.output_folder: Path | None = None

        self.track_points = []
        self.preview_results = []
        self.trip_store = trip_store or TripStore()
        self.settings = (
            settings
            if settings is not None
            else QSettings("TrailTag", "TrailTag")
        )
        saved_theme = self.settings.value("appearance/theme", "light", type=str)
        self.theme_mode = saved_theme if saved_theme in ("light", "dark") else "light"
        apply_theme(QApplication.instance(), self.theme_mode)
        self.loaded_trip_id: str | None = None
        self.loaded_trip_name: str | None = None
        self.operation_thread: QThread | None = None
        self.operation_worker: PreviewWorker | ProcessingWorker | None = None
        self.active_operation: str | None = None
        self.close_when_finished = False

        self.build_ui()
        self.set_theme(self.theme_mode, persist=False)
        self.restore_preferences()

    def build_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("appRoot")
        self.setCentralWidget(central_widget)
        self.setStyleSheet(themed_stylesheet(APP_STYLESHEET, self.theme_mode))

        appearance_menu = self.menuBar().addMenu("&Appearance")
        self.theme_actions = {}
        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.setExclusive(True)
        for mode, label in (("light", "Light mode"), ("dark", "Dark mode")):
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(mode == self.theme_mode)
            action.triggered.connect(lambda checked, mode=mode: self.set_theme(mode))
            self.theme_action_group.addAction(action)
            appearance_menu.addAction(action)
            self.theme_actions[mode] = action

        help_menu = self.menuBar().addMenu("&Help")
        self.about_action = QAction("About TrailTag", self)
        self.about_action.setMenuRole(QAction.MenuRole.AboutRole)
        self.about_action.triggered.connect(self.show_about)
        help_menu.addAction(self.about_action)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(28, 22, 28, 24)
        main_layout.setSpacing(16)

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(2)

        title = QLabel("TrailTag")
        title.setObjectName("brandTitle")

        description = QLabel(
            "Geotag your photos from a recorded GPX route."
        )
        description.setObjectName("brandSubtitle")

        brand_layout.addWidget(title)
        brand_layout.addWidget(description)

        local_badge = QLabel("LOCAL WORKFLOW  •  ORIGINALS STAY SAFE")
        local_badge.setObjectName("localBadge")
        local_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addLayout(brand_layout)
        header_layout.addStretch()
        header_layout.addWidget(local_badge)

        main_layout.addLayout(header_layout)

        # -------------------------------------------------
        # File selection card
        # -------------------------------------------------

        files_card = QFrame()
        files_card.setObjectName("card")
        files_layout = QVBoxLayout(files_card)
        files_layout.setContentsMargins(20, 16, 20, 18)
        files_layout.setSpacing(12)

        files_step = QLabel("STEP 1")
        files_step.setObjectName("stepLabel")
        files_title = QLabel("Choose your files")
        files_title.setObjectName("sectionTitle")
        files_help = QLabel(
            "Select one GPX track, the folder of original photos, and where "
            "TrailTag should save the new copies."
        )
        files_help.setObjectName("helperText")
        files_help.setWordWrap(True)

        files_layout.addWidget(files_step)
        files_layout.addWidget(files_title)
        files_layout.addWidget(files_help)

        files_grid = QGridLayout()
        files_grid.setHorizontalSpacing(12)
        files_grid.setVerticalSpacing(10)
        files_grid.setColumnStretch(1, 1)

        self.gpx_field, self.gpx_browse_button = self.create_file_picker(
            placeholder="No GPX track selected",
            button_text="Choose file",
            callback=self.select_gpx_file,
        )
        self.photo_field, self.photo_browse_button = self.create_file_picker(
            placeholder="No photo folder selected",
            button_text="Choose folder",
            callback=self.select_photo_folder,
        )
        self.output_field, self.output_browse_button = self.create_file_picker(
            placeholder="No output folder selected",
            button_text="Choose folder",
            callback=self.select_output_folder,
        )
        self.gpx_field.setAccessibleName("Selected GPX track")
        self.gpx_browse_button.setAccessibleName("Choose GPX track")
        self.gpx_browse_button.setToolTip("Choose the GPX route recorded on your trip")
        self.photo_field.setAccessibleName("Selected original photo folder")
        self.photo_browse_button.setAccessibleName("Choose original photo folder")
        self.photo_browse_button.setToolTip("Choose the folder containing your original JPEG photos")
        self.output_field.setAccessibleName("Selected output folder")
        self.output_browse_button.setAccessibleName("Choose output folder")
        self.output_browse_button.setToolTip("Choose a different folder for the new geotagged copies")

        file_rows = [
            ("GPX track", self.gpx_field, self.gpx_browse_button),
            ("Original photos", self.photo_field, self.photo_browse_button),
            ("Save new copies to", self.output_field, self.output_browse_button),
        ]

        for row, (label_text, field, button) in enumerate(file_rows):
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            files_grid.addWidget(label, row, 0)
            files_grid.addWidget(field, row, 1)
            files_grid.addWidget(button, row, 2)

        files_layout.addLayout(files_grid)

        # -------------------------------------------------
        # Timing card
        # -------------------------------------------------

        timing_card = QFrame()
        timing_card.setObjectName("card")
        timing_layout = QVBoxLayout(timing_card)
        timing_layout.setContentsMargins(20, 16, 20, 18)
        timing_layout.setSpacing(10)

        timing_step = QLabel("STEP 2")
        timing_step.setObjectName("stepLabel")
        timing_title = QLabel("Confirm the camera time")
        timing_title.setObjectName("sectionTitle")
        timing_help = QLabel(
            "Use an offset only if the camera clock was early or late."
        )
        timing_help.setObjectName("helperText")
        timing_help.setWordWrap(True)

        timing_layout.addWidget(timing_step)
        timing_layout.addWidget(timing_title)
        timing_layout.addWidget(timing_help)

        timing_grid = QGridLayout()
        timing_grid.setHorizontalSpacing(12)
        timing_grid.setVerticalSpacing(6)
        timing_grid.setColumnStretch(1, 1)

        self.timezone_combo = QComboBox()
        self.timezone_combo.setEditable(True)
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
        self.timezone_combo.setCurrentText("America/Toronto")
        self.timezone_combo.setAccessibleName("Photo timezone")
        self.timezone_combo.setToolTip(
            "The timezone the camera clock used when the photos were taken"
        )

        offset_widget = QWidget()
        offset_layout = QHBoxLayout(offset_widget)
        offset_layout.setContentsMargins(0, 0, 0, 0)
        offset_layout.setSpacing(8)
        self.offset_hours = QSpinBox()
        self.offset_hours.setRange(-23, 23)
        self.offset_hours.setSuffix(" h")
        self.offset_minutes = QSpinBox()
        self.offset_minutes.setRange(-59, 59)
        self.offset_minutes.setSuffix(" min")
        self.offset_seconds = QSpinBox()
        self.offset_seconds.setRange(-59, 59)
        self.offset_seconds.setSuffix(" sec")

        for offset_control in (
            self.offset_hours,
            self.offset_minutes,
            self.offset_seconds,
        ):
            offset_control.setMaximumWidth(105)

        offset_layout.addWidget(self.offset_hours)
        offset_layout.addWidget(self.offset_minutes)
        offset_layout.addWidget(self.offset_seconds)
        offset_layout.addStretch()

        self.max_gap = QSpinBox()
        self.max_gap.setRange(1, 120)
        self.max_gap.setValue(5)
        self.max_gap.setSuffix(" min")
        self.max_gap.setAccessibleName("Maximum GPX gap in minutes")
        self.max_gap.setToolTip(
            "Do not match a photo across a longer break in the recorded route"
        )

        timing_fields = [
            ("Photo timezone", self.timezone_combo),
            ("Camera clock offset", offset_widget),
            ("Maximum GPX gap", self.max_gap),
        ]

        for row, (label_text, field) in enumerate(timing_fields):
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            timing_grid.addWidget(label, row, 0)
            timing_grid.addWidget(field, row, 1)

        timing_layout.addLayout(timing_grid)

        self.setup_widget = QWidget()
        setup_cards_layout = QHBoxLayout(self.setup_widget)
        setup_cards_layout.setContentsMargins(0, 0, 0, 0)
        setup_cards_layout.setSpacing(16)
        setup_cards_layout.addWidget(files_card, 3)
        setup_cards_layout.addWidget(timing_card, 2)
        main_layout.addWidget(self.setup_widget)

        # -------------------------------------------------
        # Review card
        # -------------------------------------------------

        review_card = QFrame()
        review_card.setObjectName("card")
        review_layout = QVBoxLayout(review_card)
        review_layout.setContentsMargins(20, 16, 20, 18)
        review_layout.setSpacing(10)

        review_header = QHBoxLayout()
        review_title_layout = QVBoxLayout()
        review_title_layout.setSpacing(1)

        self.review_step = QLabel("STEP 3")
        self.review_step.setObjectName("stepLabel")
        self.review_title = QLabel("Review and save your trip")
        self.review_title.setObjectName("sectionTitle")

        review_title_layout.addWidget(self.review_step)
        review_title_layout.addWidget(self.review_title)

        self.status_label = QLabel(
            "Select a GPX track and photo folder to begin."
        )
        self.status_label.setObjectName("statusPill")
        self.status_label.setProperty("kind", "neutral")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        review_header.addLayout(review_title_layout)
        review_header.addStretch()
        review_header.addWidget(self.status_label)
        review_layout.addLayout(review_header)

        self.preview_tabs = QTabWidget()
        self.preview_table = PreviewTable()
        self.map_view = MapView()
        self.saved_trips_view = SavedTripsView(self.trip_store)
        self.saved_trips_view.open_trip_requested.connect(
            self.load_saved_trip
        )
        self.saved_trips_view.status_message.connect(self.set_status)
        self.saved_trips_view.trip_changed.connect(self.sync_loaded_trip)
        self.saved_trips_view.trip_deleted.connect(self.forget_deleted_trip)
        self.preview_tabs.addTab(self.preview_table, "Photo matches")
        self.preview_tabs.addTab(self.map_view, "Map preview")
        self.saved_trips_tab_index = self.preview_tabs.addTab(
            self.saved_trips_view,
            "Saved trips",
        )
        self.preview_tabs.setMinimumHeight(260)
        review_layout.addWidget(self.preview_tabs)
        main_layout.addWidget(review_card, 1)

        self.progress_widget = QFrame()
        self.progress_widget.setObjectName("operationPanel")
        progress_layout = QHBoxLayout(self.progress_widget)
        progress_layout.setContentsMargins(8, 5, 8, 5)
        progress_layout.setSpacing(10)

        self.progress_label = QLabel("Preparing…")
        self.progress_label.setObjectName("operationLabel")
        self.progress_label.setMinimumWidth(210)
        self.progress_label.setMaximumWidth(390)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("dangerAction")
        self.cancel_button.setToolTip("Stop safely after the current photo")
        self.cancel_button.clicked.connect(self.cancel_active_operation)

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar, 1)
        progress_layout.addWidget(self.cancel_button)
        self.progress_widget.hide()
        main_layout.addWidget(self.progress_widget)

        # -------------------------------------------------
        # Actions
        # -------------------------------------------------

        self.workflow_actions_widget = QWidget()
        actions_layout = QHBoxLayout(self.workflow_actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)

        safety_note = QLabel(
            "Your original photos are never modified."
        )
        safety_note.setObjectName("safetyNote")

        self.preview_button = QPushButton("Preview matches")
        self.preview_button.setObjectName("secondaryAction")
        self.preview_button.setMinimumWidth(170)
        self.preview_button.setToolTip("Check matches before creating any photo copies")
        self.preview_button.clicked.connect(self.preview_matches)

        self.save_trip_button = QPushButton("Save trip")
        self.save_trip_button.setObjectName("secondaryAction")
        self.save_trip_button.setMinimumWidth(120)
        self.save_trip_button.setEnabled(False)
        self.save_trip_button.setToolTip("Keep this route and its details in your trip library")
        self.save_trip_button.clicked.connect(self.save_current_trip)

        self.process_button = QPushButton(
            "Create geotagged copies"
        )
        self.process_button.setObjectName("primaryAction")
        self.process_button.setMinimumWidth(210)
        self.process_button.setEnabled(False)
        self.process_button.setToolTip(
            "Create new geotagged copies without changing the originals"
        )
        self.process_button.clicked.connect(self.process_photos)

        actions_layout.addWidget(safety_note)
        actions_layout.addStretch()
        actions_layout.addWidget(self.preview_button)
        actions_layout.addWidget(self.save_trip_button)
        actions_layout.addWidget(self.process_button)
        main_layout.addWidget(self.workflow_actions_widget)

        self.preview_tabs.currentChanged.connect(self.update_workspace_mode)

        # A preview belongs to the exact matching settings used to
        # create it. Changing one of those settings invalidates the
        # old results so they cannot accidentally be processed.
        self.timezone_combo.currentTextChanged.connect(
            self.clear_preview
        )

        self.offset_hours.valueChanged.connect(
            self.clear_preview
        )

        self.offset_minutes.valueChanged.connect(
            self.clear_preview
        )

        self.offset_seconds.valueChanged.connect(
            self.clear_preview
        )

        self.max_gap.valueChanged.connect(
            self.clear_preview
        )

    def set_theme(self, mode: str, *, persist: bool = True) -> None:
        if mode not in ("light", "dark"):
            return
        self.theme_mode = mode
        apply_theme(QApplication.instance(), mode)
        self.setStyleSheet(themed_stylesheet(APP_STYLESHEET, mode))
        self.theme_actions[mode].setChecked(True)
        self.preview_table.refresh_theme()
        self.saved_trips_view.photo_gallery.refresh_theme()
        for map_view in self.findChildren(MapView):
            map_view.set_theme(mode)
        self.saved_trips_view.elevation_profile.update()
        if persist:
            self.settings.setValue("appearance/theme", mode)
            self.settings.sync()

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "About TrailTag",
            (
                f"<b>TrailTag {__version__}</b><br><br>"
                "Match JPEG photos to a recorded GPX route and create "
                "geotagged copies.<br><br>"
                "Your photos and saved trips stay on this computer. "
                "Original photos and existing output files are never replaced."
                "<br><br>Maps use online OpenStreetMap tiles. The map provider "
                "receives requests for the area you view. Photo files are not uploaded."
            ),
        )

    def update_workspace_mode(self, tab_index: int) -> None:
        showing_saved_trips = tab_index == self.saved_trips_tab_index
        self.setup_widget.setVisible(not showing_saved_trips)
        self.workflow_actions_widget.setVisible(not showing_saved_trips)
        self.review_step.setText(
            "TRIP LIBRARY" if showing_saved_trips else "STEP 3"
        )
        self.review_title.setText(
            "Your saved trips"
            if showing_saved_trips
            else "Review and save your trip"
        )

    def create_file_picker(
        self,
        placeholder: str,
        button_text: str,
        callback,
    ) -> tuple[QLineEdit, QPushButton]:
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setReadOnly(True)

        button = QPushButton(button_text)
        button.setObjectName("browseButton")
        button.setMinimumWidth(100)
        button.clicked.connect(callback)

        return field, button

    def set_status(self, message: str, kind: str = "neutral"):
        self.status_label.setText(message)
        self.status_label.setProperty("kind", kind)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    # -----------------------------------------------------
    # File selection
    # -----------------------------------------------------

    def select_gpx_file(self):
        starting_folder = (
            str(self.gpx_path.parent)
            if self.gpx_path is not None
            else ""
        )
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select GPX Track",
            starting_folder,
            "GPX Files (*.gpx)",
        )

        if not file_path:
            return

        self.gpx_path = Path(
            file_path
        )

        self.loaded_trip_id = None
        self.loaded_trip_name = None
        self.save_trip_button.setText("Save trip")

        self.gpx_field.setText(
            file_path
        )

        self.clear_preview()

    def select_photo_folder(self):
        folder_path = (
            QFileDialog.getExistingDirectory(
                self,
                "Select Photo Folder",
                str(self.photo_folder or ""),
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
                str(self.output_folder or ""),
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

    def restore_preferences(self) -> None:
        controls = (self.timezone_combo, self.max_gap)
        blockers = [QSignalBlocker(control) for control in controls]

        timezone_name = self.settings.value(
            "matching/timezone",
            "America/Toronto",
            type=str,
        )
        self.timezone_combo.setCurrentText(timezone_name)
        self.max_gap.setValue(
            self.settings.value("matching/max_gap_minutes", 5, type=int)
        )

        saved_geometry = self.settings.value("window/geometry")
        if saved_geometry is not None:
            self.restoreGeometry(saved_geometry)

        saved_gpx_path = self.settings.value(
            "recent/gpx_path", "", type=str
        )
        gpx_path = Path(saved_gpx_path) if saved_gpx_path else None
        if gpx_path is not None and gpx_path.is_file():
            self.gpx_path = gpx_path
            self.gpx_field.setText(str(gpx_path))

        saved_photo_folder = self.settings.value(
            "recent/photo_folder", "", type=str
        )
        photo_folder = (
            Path(saved_photo_folder) if saved_photo_folder else None
        )
        if photo_folder is not None and photo_folder.is_dir():
            self.photo_folder = photo_folder
            self.photo_field.setText(str(photo_folder))

        saved_output_folder = self.settings.value(
            "recent/output_folder", "", type=str
        )
        output_folder = (
            Path(saved_output_folder) if saved_output_folder else None
        )
        if output_folder is not None and output_folder.is_dir():
            self.output_folder = output_folder
            self.output_field.setText(str(output_folder))

        del blockers

    def save_preferences(self) -> None:
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue(
            "matching/timezone",
            self.timezone_combo.currentText().strip(),
        )
        self.settings.setValue(
            "matching/max_gap_minutes",
            self.max_gap.value(),
        )
        if self.gpx_path is not None:
            self.settings.setValue("recent/gpx_path", str(self.gpx_path))
        if self.photo_folder is not None:
            self.settings.setValue(
                "recent/photo_folder",
                str(self.photo_folder),
            )
        if self.output_folder is not None:
            self.settings.setValue(
                "recent/output_folder",
                str(self.output_folder),
            )
        self.settings.sync()

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

        self.save_trip_button.setEnabled(False)

        self.set_status("Preview required.", "warning")

    # -----------------------------------------------------
    # Preview
    # -----------------------------------------------------

    def preview_matches(self):
        if self.gpx_path is None:
            self.set_status("Choose a GPX track to continue.", "warning")
            QMessageBox.warning(
                self,
                "Missing GPX Track",
                "Please select a GPX file.",
            )

            return

        if self.photo_folder is None:
            self.set_status("Choose a photo folder to continue.", "warning")
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
            self.set_status("Enter a photo timezone.", "warning")
            QMessageBox.warning(
                self,
                "Missing Timezone",
                "Please enter a photo timezone.",
            )

            return

        worker = PreviewWorker(
            gpx_path=self.gpx_path,
            photo_folder=self.photo_folder,
            timezone_name=timezone_name,
            time_offset=self.get_time_offset(),
            max_interpolation_gap=timedelta(
                minutes=self.max_gap.value()
            ),
        )
        self._start_operation("preview", worker)

    # -----------------------------------------------------
    # Saved trips
    # -----------------------------------------------------

    def save_current_trip(self):
        if not self.track_points:
            self.set_status("Preview a route before saving it.", "warning")
            QMessageBox.warning(
                self,
                "No Trip to Save",
                "Preview a GPX route before saving a trip.",
            )
            return

        default_name = self.loaded_trip_name or (
            self.gpx_path.stem.replace("_", " ").replace("-", " ").strip()
            if self.gpx_path is not None
            else "My trip"
        )
        trip_name, accepted = QInputDialog.getText(
            self,
            "Save Trip",
            "Trip name:",
            text=default_name,
        )

        if not accepted:
            return

        trip_name = trip_name.strip()
        if not trip_name:
            self.set_status("Enter a name for this trip.", "warning")
            QMessageBox.warning(
                self,
                "Trip Name Required",
                "Please enter a name for this trip.",
            )
            return

        trip = create_saved_trip(
            name=trip_name,
            gpx_path=self.gpx_path,
            photo_folder=self.photo_folder,
            output_folder=self.output_folder,
            timezone_name=self.timezone_combo.currentText().strip(),
            time_offset_seconds=int(self.get_time_offset().total_seconds()),
            max_gap_minutes=self.max_gap.value(),
            track_points=self.track_points,
            preview_results=self.preview_results,
        )
        if self.loaded_trip_id is not None:
            trip.trip_id = self.loaded_trip_id

        try:
            self.trip_store.save_trip(trip)
        except TripStoreError as error:
            self.set_status("Trip could not be saved.", "error")
            QMessageBox.critical(self, "Save Failed", str(error))
            return

        self.saved_trips_view.refresh(select_trip_id=trip.trip_id)
        self.loaded_trip_id = trip.trip_id
        self.loaded_trip_name = trip.name
        self.save_trip_button.setText("Update trip")
        self.preview_tabs.setCurrentIndex(self.saved_trips_tab_index)
        self.set_status(f'“{trip.name}” saved on this computer.', "success")

    def load_saved_trip(self, trip: SavedTrip) -> None:
        controls = (
            self.timezone_combo,
            self.offset_hours,
            self.offset_minutes,
            self.offset_seconds,
            self.max_gap,
        )
        blockers = [QSignalBlocker(control) for control in controls]

        self.gpx_path = trip.gpx_path
        self.photo_folder = trip.photo_folder
        self.output_folder = trip.output_folder
        self.gpx_field.setText(_display_path(trip.gpx_path))
        self.photo_field.setText(_display_path(trip.photo_folder))
        self.output_field.setText(_display_path(trip.output_folder))
        self.timezone_combo.setCurrentText(trip.timezone_name)

        sign = -1 if trip.time_offset_seconds < 0 else 1
        offset = abs(trip.time_offset_seconds)
        hours, offset = divmod(offset, 3_600)
        minutes, seconds = divmod(offset, 60)
        self.offset_hours.setValue(sign * hours)
        self.offset_minutes.setValue(sign * minutes)
        self.offset_seconds.setValue(sign * seconds)
        self.max_gap.setValue(trip.max_gap_minutes)

        del blockers

        self.track_points = list(trip.track_points)
        self.preview_results = list(trip.preview_results)
        self.loaded_trip_id = trip.trip_id
        self.loaded_trip_name = trip.name
        self.preview_table.set_results(self.preview_results)
        self.map_view.set_results(self.track_points, self.preview_results)

        matched = sum(result.matched for result in self.preview_results)
        self.process_button.setEnabled(matched > 0)
        self.save_trip_button.setEnabled(bool(self.track_points))
        self.save_trip_button.setText("Update trip")
        self.preview_tabs.setCurrentIndex(0)

        missing_sources = _count_missing_sources(trip)
        if missing_sources:
            self.set_status(
                f'Loaded “{trip.name}”  •  {missing_sources} source items unavailable',
                "warning",
            )
        else:
            self.set_status(f'Loaded “{trip.name}” for editing.', "success")

    def sync_loaded_trip(self, trip: SavedTrip) -> None:
        if self.loaded_trip_id != trip.trip_id:
            return

        self.loaded_trip_name = trip.name
        self.photo_folder = trip.photo_folder
        self.preview_results = list(trip.preview_results)
        self.photo_field.setText(_display_path(trip.photo_folder))
        self.preview_table.set_results(self.preview_results)
        self.map_view.set_results(self.track_points, self.preview_results)

    def forget_deleted_trip(self, trip_id: str) -> None:
        if self.loaded_trip_id != trip_id:
            return

        self.loaded_trip_id = None
        self.loaded_trip_name = None
        self.save_trip_button.setText("Save trip")

    # -----------------------------------------------------
    # Processing
    # -----------------------------------------------------

    def process_photos(self):
        if not self.preview_results:
            self.set_status("Preview the photos first.", "warning")
            QMessageBox.warning(
                self,
                "No Preview",
                "Preview the photos before processing.",
            )

            return

        if self.output_folder is None:
            self.set_status("Choose where to save the new copies.", "warning")
            QMessageBox.warning(
                self,
                "Missing Output Folder",
                "Please select an output folder.",
            )

            return

        worker = ProcessingWorker(
            preview_results=self.preview_results,
            output_folder=self.output_folder,
        )
        self._start_operation("process", worker)

    # -----------------------------------------------------
    # Background operations
    # -----------------------------------------------------

    def _start_operation(
        self,
        operation: str,
        worker: PreviewWorker | ProcessingWorker,
    ) -> None:
        if self.operation_thread is not None:
            return

        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._operation_progress)
        worker.completed.connect(self._operation_completed)
        worker.cancelled.connect(self._operation_cancelled)
        worker.failed.connect(self._operation_failed)
        worker.completed.connect(thread.quit)
        worker.cancelled.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.completed.connect(worker.deleteLater)
        worker.cancelled.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._operation_thread_finished)

        self.operation_thread = thread
        self.operation_worker = worker
        self.active_operation = operation
        self._set_operation_controls(active=True)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("Working…")
        self.progress_label.setText(
            "Preparing photo matches…"
            if operation == "preview"
            else "Preparing geotagged copies…"
        )
        self.cancel_button.setEnabled(True)
        self.progress_widget.show()
        self.set_status(
            "Generating preview in the background…"
            if operation == "preview"
            else "Creating geotagged copies in the background…",
            "busy",
        )
        thread.start()

    def _operation_progress(
        self,
        current: int,
        total: int,
        photo_name: str,
    ) -> None:
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
            self.progress_bar.setFormat("%v of %m")
        else:
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setFormat("No photos found")

        verb = "Matching" if self.active_operation == "preview" else "Writing"
        display_name = _shorten_photo_name(photo_name)
        self.progress_label.setText(
            f"{verb} {current} of {total}  •  {display_name}"
            if total
            else display_name
        )

    def _operation_completed(self, payload: object) -> None:
        operation = self.active_operation

        if operation == "preview" and isinstance(payload, PreviewBatch):
            self.track_points = payload.track_points
            self.preview_results = payload.preview_results
            self.preview_table.set_results(self.preview_results)
            self.map_view.set_results(
                self.track_points,
                self.preview_results,
            )

            matched = sum(result.matched for result in self.preview_results)
            errors = [
                result
                for result in self.preview_results
                if result.status.startswith("Preview failed:")
            ]
            unmatched = len(self.preview_results) - matched
            status_kind = "success" if matched and not errors else "warning"
            message = (
                f"{len(self.preview_results)} photos  •  "
                f"{matched} matched  •  {unmatched} unmatched"
            )
            if errors:
                message += f"  •  {len(errors)} errors"
            self.set_status(message, status_kind)

            if errors and not self.close_when_finished:
                details = "\n".join(
                    f"• {result.source_path.name}: {result.status}"
                    for result in errors[:8]
                )
                if len(errors) > 8:
                    details += f"\n• …and {len(errors) - 8} more"
                QMessageBox.warning(
                    self,
                    "Preview Complete with Issues",
                    (
                        "TrailTag finished the preview and kept going when "
                        "individual photos failed.\n\n"
                        f"{details}"
                    ),
                )

        elif operation == "process" and isinstance(payload, list):
            self._show_processing_report(payload)

        self._set_operation_controls(active=False)

    def _operation_cancelled(self, payload: object) -> None:
        operation = self.active_operation

        if operation == "process" and isinstance(payload, list):
            successful, skipped, failed = _processing_counts(payload)
            self.set_status(
                f"Cancelled safely  •  {successful} copies completed",
                "warning",
            )
            if not self.close_when_finished:
                QMessageBox.information(
                    self,
                    "Processing Cancelled",
                    (
                        "TrailTag stopped before starting another photo.\n\n"
                        f"{successful} geotagged copies completed\n"
                        f"{skipped} skipped\n"
                        f"{failed} failed\n\n"
                        "Completed copies were kept and originals were unchanged."
                    ),
                )
        else:
            self.set_status("Preview cancelled. No results were changed.", "warning")

        self._set_operation_controls(active=False)

    def _operation_failed(self, error_message: str) -> None:
        operation_name = (
            "Preview" if self.active_operation == "preview" else "Processing"
        )
        self.set_status(f"{operation_name} failed.", "error")
        self._set_operation_controls(active=False)
        if not self.close_when_finished:
            QMessageBox.critical(
                self,
                f"{operation_name} Failed",
                error_message,
            )

    def _operation_thread_finished(self) -> None:
        self.operation_thread = None
        self.operation_worker = None
        self.active_operation = None

        if self.close_when_finished:
            self.close_when_finished = False
            QTimer.singleShot(0, self.close)

    def _set_operation_controls(self, *, active: bool) -> None:
        enabled = not active
        for control in (
            self.gpx_browse_button,
            self.photo_browse_button,
            self.output_browse_button,
            self.timezone_combo,
            self.offset_hours,
            self.offset_minutes,
            self.offset_seconds,
            self.max_gap,
            self.preview_tabs,
        ):
            control.setEnabled(enabled)

        if active:
            self.preview_button.setEnabled(False)
            self.process_button.setEnabled(False)
            self.save_trip_button.setEnabled(False)
            return

        self.progress_widget.hide()
        self.preview_button.setEnabled(True)
        matched = sum(result.matched for result in self.preview_results)
        self.process_button.setEnabled(matched > 0)
        self.save_trip_button.setEnabled(bool(self.track_points))

    def cancel_active_operation(self) -> None:
        if self.operation_worker is None:
            return
        self.cancel_button.setEnabled(False)
        self.progress_label.setText(
            "Cancelling safely after the current photo…"
        )
        self.operation_worker.cancel()

    def _show_processing_report(
        self,
        results: list[ProcessResult],
    ) -> None:
        successful, skipped, failed = _processing_counts(results)
        status_kind = "success" if failed == 0 else "warning"
        self.set_status(
            f"{len(results)} processed  •  {successful} geotagged  •  "
            f"{skipped} skipped  •  {failed} failed",
            status_kind,
        )

        problem_results = [result for result in results if not result.success]
        problem_summary = ""
        if problem_results:
            problem_summary = "\n\nDetails:\n" + "\n".join(
                f"• {result.photo_name}: {result.status}"
                for result in problem_results[:8]
            )
            if len(problem_results) > 8:
                problem_summary += (
                    f"\n• …and {len(problem_results) - 8} more"
                )

        message = (
            f"{successful} successfully geotagged\n"
            f"{skipped} skipped\n"
            f"{failed} failed"
            f"{problem_summary}"
        )
        if failed:
            QMessageBox.warning(self, "Processing Complete", message)
        else:
            QMessageBox.information(self, "Processing Complete", message)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.operation_thread is not None and self.operation_thread.isRunning():
            answer = QMessageBox.question(
                self,
                "TrailTag Is Still Working",
                (
                    "Cancel the current operation and close TrailTag?\n\n"
                    "TrailTag will finish the current photo before closing."
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.close_when_finished = True
                self.cancel_active_operation()
                self.set_status("Cancelling safely before closing…", "warning")
            event.ignore()
            return

        self.save_preferences()
        super().closeEvent(event)


def _display_path(path: Path | None) -> str:
    if path is None:
        return ""
    suffix = "" if path.exists() else "  •  Not found"
    return f"{path}{suffix}"


def _count_missing_sources(trip: SavedTrip) -> int:
    missing = 0
    if trip.gpx_path is not None and not trip.gpx_path.is_file():
        missing += 1
    missing += sum(
        not result.source_path.is_file()
        for result in trip.preview_results
    )
    return missing


def _processing_counts(
    results: list[ProcessResult],
) -> tuple[int, int, int]:
    successful = sum(result.success for result in results)
    skipped = sum(
        result.status.startswith("Skipped:")
        for result in results
    )
    failed = len(results) - successful - skipped
    return successful, skipped, failed


def _shorten_photo_name(photo_name: str, limit: int = 42) -> str:
    if len(photo_name) <= limit:
        return photo_name
    return f"{photo_name[: limit - 1]}…"
