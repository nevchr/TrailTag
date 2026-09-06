from pathlib import Path

from PySide6.QtCore import QSize, Qt, QSignalBlocker, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QImageReader, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QListView, QListWidget, QListWidgetItem

from ..preview import PreviewResult
from .theme import theme_colors


class PhotoGallery(QListWidget):
    photo_selected = Signal(int)

    def __init__(self):
        super().__init__()

        self.results: list[PreviewResult] = []
        self.items_by_index: dict[int, QListWidgetItem] = {}
        self.pending_thumbnails: list[tuple[int, Path]] = []
        self.thumbnail_cursor = 0
        self.generation = 0

        self.setObjectName("photoGallery")
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setMovement(QListView.Movement.Static)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setIconSize(QSize(138, 92))
        self.setGridSize(QSize(158, 128))
        self.setSpacing(4)
        self.setWordWrap(True)
        self.itemClicked.connect(self._emit_selection)

    def set_results(self, results: list[PreviewResult]) -> None:
        self.generation += 1
        generation = self.generation
        self.results = list(results)
        self.items_by_index = {}
        self.pending_thumbnails = []
        self.thumbnail_cursor = 0
        self.clear()

        placeholder = _placeholder_pixmap(self.iconSize())
        for index, result in enumerate(self.results):
            item = QListWidgetItem(
                QIcon(placeholder),
                result.source_path.name,
            )
            item.setData(Qt.ItemDataRole.UserRole, index)
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
            item.setToolTip(f"{result.source_path}\n{result.status}")
            item.setForeground(
                QColor(theme_colors()["accent" if result.matched else "negative"])
            )
            self.addItem(item)
            self.items_by_index[index] = item
            self.pending_thumbnails.append((index, result.source_path))

        if self.pending_thumbnails:
            QTimer.singleShot(
                0,
                lambda: self._load_next_thumbnail(generation),
            )

    def refresh_theme(self) -> None:
        colors = theme_colors()
        for index, item in self.items_by_index.items():
            item.setForeground(QColor(colors[
                "accent" if self.results[index].matched else "negative"
            ]))

    def select_photo(self, index: int) -> None:
        item = self.items_by_index.get(index)
        if item is None:
            return
        blocker = QSignalBlocker(self)
        self.setCurrentItem(item)
        self.scrollToItem(item)
        del blocker

    def _emit_selection(self, item: QListWidgetItem) -> None:
        index = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(index, int):
            self.photo_selected.emit(index)

    def _load_next_thumbnail(self, generation: int) -> None:
        if generation != self.generation:
            return
        if self.thumbnail_cursor >= len(self.pending_thumbnails):
            return

        index, photo_path = self.pending_thumbnails[self.thumbnail_cursor]
        self.thumbnail_cursor += 1
        image = _read_thumbnail(photo_path, self.iconSize())
        item = self.items_by_index.get(index)
        if item is not None and image is not None:
            item.setIcon(QIcon(image))

        QTimer.singleShot(
            1,
            lambda: self._load_next_thumbnail(generation),
        )


def _read_thumbnail(photo_path: Path, size: QSize) -> QPixmap | None:
    reader = QImageReader(str(photo_path))
    reader.setAutoTransform(True)
    original_size = reader.size()
    if original_size.isValid():
        reader.setScaledSize(
            original_size.scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
            )
        )

    image = reader.read()
    if image.isNull():
        return None

    canvas = QPixmap(size)
    canvas.fill(QColor("#edf3f0"))
    pixmap = QPixmap.fromImage(image)
    x = (size.width() - pixmap.width()) // 2
    y = (size.height() - pixmap.height()) // 2
    painter = QPainter(canvas)
    painter.drawPixmap(x, y, pixmap)
    painter.end()
    return canvas


def _placeholder_pixmap(size: QSize) -> QPixmap:
    pixmap = QPixmap(size)
    pixmap.fill(QColor("#edf3f0"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#8aa196"), 2))
    frame = pixmap.rect().adjusted(44, 27, -44, -27)
    painter.drawRoundedRect(frame, 5, 5)
    painter.drawEllipse(frame.center(), 9, 9)
    painter.end()
    return pixmap
