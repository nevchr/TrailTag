import os
import re
import time
from datetime import datetime
from pathlib import Path

import piexif
import pytest
from PIL import Image


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QMessageBox, QInputDialog

from src.geotagger.preview import PreviewResult
from src.geotagger.gpx_parser import TrackPoint
from src.geotagger.trip_store import TripStore
from src.geotagger.ui.main_window import MainWindow
from src.geotagger.ui.map_view import MapView, PhotoBridge
from src.geotagger.ui.theme import THEMES, theme_colors, themed_stylesheet
from src.geotagger.ui.main_window import APP_STYLESHEET


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def create_test_window(tmp_path, store=None, settings_path=None):
    settings = QSettings(
        str(settings_path or (tmp_path / "settings.ini")),
        QSettings.Format.IniFormat,
    )
    return MainWindow(
        store or TripStore(tmp_path / "trips.json"),
        settings=settings,
    )


def test_matching_setting_change_invalidates_preview(qt_app, tmp_path):
    window = create_test_window(tmp_path)

    try:
        window.preview_results = [object()]
        window.process_button.setEnabled(True)

        window.offset_seconds.setValue(1)

        assert window.windowTitle() == "TrailTag"
        assert window.preview_results == []
        assert window.process_button.isEnabled() is False
        assert window.save_trip_button.isEnabled() is False
        assert window.status_label.text() == "Preview required."
        assert window.status_label.property("kind") == "warning"
    finally:
        window.close()


def test_window_presents_guided_three_step_workflow(qt_app, tmp_path):
    window = create_test_window(tmp_path)

    try:
        assert window.preview_tabs.tabText(0) == "Photo matches"
        assert window.preview_tabs.tabText(1) == "Map preview"
        assert window.preview_tabs.tabText(2) == "Saved trips"
        assert window.gpx_browse_button.text() == "Choose file"
        assert window.photo_browse_button.text() == "Choose folder"
        assert window.preview_button.objectName() == "secondaryAction"
        assert window.process_button.objectName() == "primaryAction"
        assert window.status_label.property("kind") == "neutral"
    finally:
        window.close()


def test_preview_table_visually_distinguishes_match_status(qt_app, tmp_path):
    window = create_test_window(tmp_path)
    results = [
        PreviewResult(
            source_path=Path("matched.jpg"),
            photo_time=datetime(2026, 1, 1, 12, 0),
            adjusted_time=datetime(2026, 1, 1, 17, 0),
            latitude=43.65,
            longitude=-79.38,
            elevation=90.0,
            matched=True,
            status="Matched",
        ),
        PreviewResult(
            source_path=Path("unmatched.jpg"),
            photo_time=datetime(2026, 1, 1, 12, 1),
            adjusted_time=datetime(2026, 1, 1, 17, 1),
            latitude=None,
            longitude=None,
            elevation=None,
            matched=False,
            status="No GPX match",
        ),
    ]

    try:
        window.preview_table.set_results(results)

        assert window.preview_table.verticalHeader().isHidden()
        assert (
            window.preview_table.item(0, 6).foreground().color().name()
            == "#176b4d"
        )
        assert (
            window.preview_table.item(1, 6).foreground().color().name()
            == "#9a3d32"
        )
    finally:
        window.close()


def test_named_trip_can_be_saved_and_viewed_after_reload(
    qt_app,
    tmp_path,
    monkeypatch,
):
    store = TripStore(tmp_path / "trips.json")
    window = create_test_window(tmp_path, store)
    start = datetime.fromisoformat("2026-09-04T13:00:00+00:00")

    try:
        window.gpx_path = Path("harbour-route.gpx")
        window.photo_folder = Path("photos")
        window.track_points = [
            TrackPoint(43.64, -79.38, 78.0, start),
            TrackPoint(43.65, -79.38, 82.0, start.replace(hour=14)),
        ]
        window.preview_results = [
            PreviewResult(
                source_path=Path("old-photos/trail.jpg"),
                photo_time=datetime(2026, 9, 4, 9, 30),
                adjusted_time=start.replace(minute=30),
                latitude=43.645,
                longitude=-79.38,
                elevation=80.0,
                matched=True,
                status="Matched",
            )
        ]
        monkeypatch.setattr(
            "src.geotagger.ui.main_window.QInputDialog.getText",
            lambda *args, **kwargs: ("Harbour walk", True),
        )

        window.save_current_trip()

        reloaded_trips = TripStore(store.path).load_trips()
        assert [trip.name for trip in reloaded_trips] == ["Harbour walk"]
        assert window.saved_trips_view.trip_list.count() == 1
        assert window.saved_trips_view.trip_title.text() == "Harbour walk"
        assert window.saved_trips_view.duration_value.text() == "1 h 0 min"
        assert window.saved_trips_view.elevation_gain_value.text() == "4 m"
        assert window.saved_trips_view.average_speed_value.text().endswith("km/h")
        assert window.saved_trips_view.photo_gallery.count() == 1
        assert window.preview_tabs.currentIndex() == window.saved_trips_tab_index
        assert window.setup_widget.isHidden() is True
        assert window.workflow_actions_widget.isHidden() is True
        assert window.status_label.property("kind") == "success"

        window.saved_trips_view.open_button.click()

        assert window.preview_tabs.currentIndex() == 0
        assert window.setup_widget.isHidden() is False
        assert window.loaded_trip_id == reloaded_trips[0].trip_id
        assert window.timezone_combo.currentText() == "America/Toronto"
        assert window.save_trip_button.text() == "Update trip"

        window.preview_tabs.setCurrentIndex(window.saved_trips_tab_index)
        window.saved_trips_view.photo_gallery.photo_selected.emit(0)
        assert window.saved_trips_view.elevation_profile.selected_distance is not None
        window.saved_trips_view.map_view.photo_selected.emit(0)
        assert (
            window.saved_trips_view.photo_gallery.currentItem().text()
            == "trail.jpg"
        )

        monkeypatch.setattr(
            "src.geotagger.ui.saved_trips_view.QInputDialog.getText",
            lambda *args, **kwargs: ("Island afternoon", True),
        )
        window.saved_trips_view.rename_button.click()
        assert store.load_trips()[0].name == "Island afternoon"
        assert window.loaded_trip_name == "Island afternoon"

        new_photo_folder = tmp_path / "reconnected"
        new_photo_folder.mkdir()
        (new_photo_folder / "trail.jpg").write_bytes(b"photo")
        monkeypatch.setattr(
            "src.geotagger.ui.saved_trips_view.QFileDialog.getExistingDirectory",
            lambda *args, **kwargs: str(new_photo_folder),
        )
        window.saved_trips_view.reconnect_button.click()
        reconnected_trip = store.load_trips()[0]
        assert reconnected_trip.photo_folder == new_photo_folder
        assert (
            reconnected_trip.preview_results[0].source_path
            == new_photo_folder / "trail.jpg"
        )
        assert window.photo_folder == new_photo_folder

        monkeypatch.setattr(
            "src.geotagger.ui.saved_trips_view.QMessageBox.question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )
        window.saved_trips_view.delete_button.click()
        assert store.load_trips() == []
        assert (new_photo_folder / "trail.jpg").exists()
        assert window.loaded_trip_id is None
        assert window.save_trip_button.text() == "Save trip"
    finally:
        window.close()


def test_preview_runs_in_background_with_visible_progress(qt_app, tmp_path):
    gpx_path = tmp_path / "route.gpx"
    gpx_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="TrailTag test"
     xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="43.6400" lon="-79.3800">
      <ele>78</ele><time>2026-09-04T13:00:00Z</time>
    </trkpt>
    <trkpt lat="43.6500" lon="-79.3800">
      <ele>82</ele><time>2026-09-04T13:00:30Z</time>
    </trkpt>
  </trkseg></trk>
</gpx>
""",
        encoding="utf-8",
    )
    photo_path = tmp_path / "trail.jpg"
    exif = {
        "0th": {},
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: b"2026:09:04 09:00:15",
        },
        "GPS": {},
        "1st": {},
        "thumbnail": None,
    }
    Image.new("RGB", (8, 8), "green").save(
        photo_path,
        "JPEG",
        exif=piexif.dump(exif),
    )

    window = create_test_window(tmp_path)
    try:
        window.gpx_path = gpx_path
        window.photo_folder = tmp_path
        window.preview_matches()

        assert window.operation_thread is not None
        assert window.progress_widget.isHidden() is False
        assert window.preview_button.isEnabled() is False

        deadline = time.monotonic() + 5
        while window.operation_thread is not None and time.monotonic() < deadline:
            qt_app.processEvents()
            time.sleep(0.01)

        assert window.operation_thread is None
        assert window.progress_widget.isHidden() is True
        assert len(window.preview_results) == 1
        assert window.preview_results[0].matched is True
        assert window.process_button.isEnabled() is True
    finally:
        window.close()


def test_map_marker_selection_is_sent_back_to_the_gallery(qt_app):
    bridge = PhotoBridge()
    selected = []
    bridge.photo_selected.connect(selected.append)
    bridge.selectPhoto(4)
    assert selected == [4]


def test_map_click_before_page_ready_is_replayed(qt_app, monkeypatch):
    view = MapView()
    view.preview_results = [object()]
    applied = []
    selected = []
    monkeypatch.setattr(view, "_apply_photo_popup", applied.append)
    view.photo_selected.connect(selected.append)
    try:
        view.photo_bridge.selectPhoto(0)
        assert applied == []
        assert view.pending_photo_index == 0
        assert selected == [0]
        view._map_loaded(True)
        assert applied == [0]
        assert view.pending_photo_index is None
        view.photo_bridge.selectPhoto(-1)
        view.photo_bridge.selectPhoto(99)
        assert selected == [0]
    finally:
        view.close()
        view.deleteLater()


def wait_until(qt_app, condition, timeout=10):
    deadline = time.monotonic() + timeout
    while not condition() and time.monotonic() < deadline:
        qt_app.processEvents()
        time.sleep(0.01)
    assert condition(), "Timed out waiting for the browser"


def browser_value(qt_app, view, script):
    values = []
    view.page().runJavaScript(script, values.append)
    wait_until(qt_app, lambda: bool(values))
    return values[0]


def test_real_browser_clicks_load_previews_without_navigation(qt_app, tmp_path, monkeypatch):
    # Only replace the online mapping library. Exercise the real Qt browser,
    # bundled WebChannel JS, Python slots, thumbnail generator and popup update.
    leaflet_stub = """
    window.testMarkers = [];
    window.L = {
        map: () => ({fitBounds() {}, setView() {}, getZoom() { return 15; }}),
        tileLayer: () => ({on() {return this;}, addTo() {return this;}}),
        polyline: () => ({addTo() {return this;}, getBounds() {return [];}}),
        marker: () => {
            const marker = {
                addTo() {return this;},
                bindPopup(content) {this.content = content; return this;},
                on(event, handler) {this[event] = handler; return this;},
                setPopupContent(content) {this.content = content;},
                openPopup() {document.getElementById('map').innerHTML = this.content;},
                getPopup() {return {getContent: () => this.content};},
                getLatLng() {return [43.64, -79.38];}
            };
            window.testMarkers.push(marker);
            return marker;
        }
    };
    """
    view = MapView()
    original_set_html = view.setHtml

    def offline_html(page):
        page = re.sub(r'<link\s+rel="stylesheet".*?/>', '', page, flags=re.S)
        page = re.sub(r'<script\s+src="https://unpkg.com/leaflet.*?</script>',
                      '<script>' + leaflet_stub + '</script>', page, flags=re.S)
        original_set_html(page)

    monkeypatch.setattr(view, "setHtml", offline_html)
    photo = tmp_path / "trail.jpg"
    Image.new("RGB", (32, 24), "green").save(photo)
    start = datetime.fromisoformat("2026-09-04T13:00:00+00:00")
    results = [PreviewResult(path, start, start, 43.64, -79.38, 78., True, "Matched")
               for path in (photo, tmp_path / "missing.jpg")]
    selected = []
    view.photo_selected.connect(selected.append)
    try:
        view.set_results([TrackPoint(43.64, -79.38, 78., start)], results)
        wait_until(qt_app, lambda: view.page_ready)
        assert browser_value(qt_app, view, "window.testMarkers.length") == 2
        for index in (0, 1, 0):
            count = len(selected)
            view.page().runJavaScript(f"window.testMarkers[{index}].click();")
            wait_until(qt_app, lambda: len(selected) > count)
            assert selected[-1] == index
            content = browser_value(qt_app, view, "document.getElementById('map').innerHTML")
            assert "Loading photo preview" not in content
            if index == 0:
                assert "data:image/jpeg;base64," in content
                assert browser_value(qt_app, view,
                    "document.querySelector('img').complete && document.querySelector('img').naturalWidth > 0")
            else:
                assert "Photo preview unavailable" in content
            assert view.page_ready
        # Selecting through the gallery uses the same popup renderer.
        view.focus_photo(0)
        assert "data:image/jpeg;base64," in browser_value(qt_app, view,
            "document.getElementById('map').innerHTML")
        for mode, expected in (("dark", "rgb(237, 247, 241)"),
                               ("light", "rgb(24, 53, 43)")):
            view.set_theme(mode)
            assert browser_value(qt_app, view,
                "getComputedStyle(document.querySelector('.photo-name')).color") == expected
            assert "data:image/jpeg;base64," in browser_value(qt_app, view,
                "document.getElementById('map').innerHTML")
            assert view.page_ready
    finally:
        view.close()
        view.deleteLater()


def test_light_ui_overrides_inherited_dark_text_colors(qt_app, tmp_path):
    dark = QPalette()
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText,
                 QPalette.ColorRole.ButtonText):
        dark.setColor(role, QColor("white"))
    dark.setColor(QPalette.ColorRole.Base, QColor("#202020"))
    qt_app.setPalette(dark)
    window = create_test_window(tmp_path)
    dialog = QInputDialog(window)
    try:
        window.show()
        qt_app.processEvents()
        for widget in (window.preview_table, window.saved_trips_view.photo_gallery,
                       window.timezone_combo.view(), dialog, window.menuBar()):
            widget.ensurePolished()
            for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
                assert widget.palette().color(group, QPalette.ColorRole.Text).lightness() < 128
                assert widget.palette().color(group, QPalette.ColorRole.WindowText).lightness() < 128
        assert window.preview_table.palette().color(QPalette.ColorRole.Base).name() == "#ffffff"
    finally:
        dialog.close()
        window.close()


def test_theme_switch_updates_existing_results_and_survives_restart(qt_app, tmp_path):
    window = create_test_window(tmp_path)
    results = [PreviewResult(Path("photo.jpg"), None, None, 43., -79., 0., True, "Matched")]
    window.preview_table.set_results(results)
    window.saved_trips_view.photo_gallery.set_results(results)
    try:
        assert not window.windowIcon().isNull()
        assert not window.windowIcon().pixmap(32, 32).isNull()
        for mode in ("dark", "light", "dark"):
            window.theme_actions[mode].trigger()
            qt_app.processEvents()
            colors = theme_colors(mode)
            assert window.theme_mode == mode
            assert window.theme_actions[mode].isChecked()
            assert window.preview_table.item(0, 6).foreground().color().name() == colors["accent"]
            assert window.saved_trips_view.photo_gallery.item(0).foreground().color().name() == colors["accent"]
            assert window.map_view.theme_mode == mode
            assert window.saved_trips_view.map_view.theme_mode == mode
            assert window.preview_table.rowCount() == 1
            window.gpx_field.ensurePolished()
            assert window.gpx_field.palette().color(QPalette.ColorRole.PlaceholderText).name() == colors["muted"]
    finally:
        window.close()
    restored = create_test_window(tmp_path)
    try:
        assert restored.theme_mode == "dark"
        assert restored.theme_actions["dark"].isChecked()
    finally:
        restored.set_theme("light")
        restored.close()


def contrast_ratio(foreground, background):
    def luminance(color):
        channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
                  for v in channels]
        return sum(v * weight for v, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_theme_text_has_at_least_4_5_to_1_contrast(mode):
    colors = THEMES[mode]
    for foreground in ("text", "muted", "accent", "negative"):
        for background in ("window", "surface", "raised", "button"):
            assert contrast_ratio(colors[foreground], colors[background]) >= 4.5, (mode, foreground, background)
    for foreground, background in (("text", "highlight"), ("accent", "positive_bg"),
                                  ("negative", "negative_bg"), ("warning", "warning_bg")):
        assert contrast_ratio(colors[foreground], colors[background]) >= 4.5
    stylesheet = themed_stylesheet(APP_STYLESHEET, mode)
    # Check explicit text/background pairs, including primary/disabled buttons.
    # Earlier primary-action declarations are superseded by dark overrides.
    for selector, declarations in re.findall(r"([^{}]+)\{([^{}]+)\}", stylesheet):
        foreground = re.search(r"(?:^|[;\s])color:\s*(#[0-9a-f]{6})", declarations)
        background = re.search(r"(?:^|[;\s])background:\s*(#[0-9a-f]{6})", declarations)
        if foreground and background:
            if mode == "dark" and "primaryAction" in selector and foreground[1] == colors["surface"]:
                continue
            assert contrast_ratio(foreground[1], background[1]) >= 4.5, (mode, selector.strip())


def test_window_preferences_are_restored_after_restart(qt_app, tmp_path):
    settings_path = tmp_path / "preferences.ini"
    gpx_path = tmp_path / "last-route.gpx"
    photo_folder = tmp_path / "photos"
    output_folder = tmp_path / "output"
    gpx_path.write_text("<gpx></gpx>", encoding="utf-8")
    photo_folder.mkdir()
    output_folder.mkdir()

    window = create_test_window(tmp_path, settings_path=settings_path)
    window.gpx_path = gpx_path
    window.photo_folder = photo_folder
    window.output_folder = output_folder
    window.timezone_combo.setCurrentText("America/Vancouver")
    window.max_gap.setValue(12)
    window.resize(1100, 760)
    window.close()

    restored = create_test_window(tmp_path, settings_path=settings_path)
    try:
        assert restored.gpx_path == gpx_path
        assert restored.photo_folder == photo_folder
        assert restored.output_folder == output_folder
        assert restored.timezone_combo.currentText() == "America/Vancouver"
        assert restored.max_gap.value() == 12
        saved_geometry = QSettings(
            str(settings_path),
            QSettings.Format.IniFormat,
        ).value("window/geometry")
        assert saved_geometry is not None
        assert not saved_geometry.isEmpty()
        assert restored.size().width() >= restored.minimumWidth()
        assert restored.size().height() >= restored.minimumHeight()
    finally:
        restored.close()
