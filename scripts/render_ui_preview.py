import os
import sys
import tempfile
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QPoint, QSettings
from PySide6.QtGui import QFontDatabase, QImage, QPainter
from PySide6.QtWidgets import QApplication

from src.geotagger.ui.main_window import MainWindow
from src.geotagger.trip_store import TripStore


app = QApplication.instance() or QApplication([])
if sys.platform == "win32":
    for font_name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf"):
        font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / font_name
        if font_path.is_file():
            QFontDatabase.addApplicationFont(str(font_path))
trip_store = None
if len(sys.argv) >= 6:
    trip_store = TripStore(Path(sys.argv[5]))

preview_temp = tempfile.TemporaryDirectory(prefix="trailtag-ui-")
settings = QSettings(
    str(Path(preview_temp.name) / "settings.ini"),
    QSettings.Format.IniFormat,
)
window = MainWindow(trip_store, settings=settings)
if len(sys.argv) >= 4:
    window.resize(int(sys.argv[2]), int(sys.argv[3]))
if len(sys.argv) >= 5:
    window.preview_tabs.setCurrentIndex(int(sys.argv[4]))
if len(sys.argv) >= 7:
    window.saved_trips_view.visual_tabs.setCurrentIndex(int(sys.argv[6]))
window.ensurePolished()
app.processEvents()

output_path = Path(sys.argv[1]).resolve()
output_path.parent.mkdir(parents=True, exist_ok=True)

image = QImage(window.size(), QImage.Format.Format_ARGB32)
image.fill(0xFFFFFFFF)
painter = QPainter(image)
window.render(painter, QPoint())
painter.end()

if not image.save(str(output_path), "PNG"):
    raise RuntimeError("The UI preview image could not be saved.")

window.close()
preview_temp.cleanup()
