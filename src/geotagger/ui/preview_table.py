from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from ..preview import PreviewResult
from .theme import theme_colors


class PreviewTable(QTableWidget):
    def __init__(self):
        super().__init__()

        self.setColumnCount(7)

        self.setHorizontalHeaderLabels(
            [
                "Photo",
                "Photo Time",
                "Adjusted Time",
                "Latitude",
                "Longitude",
                "Elevation",
                "Status",
            ]
        )

        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setCornerButtonEnabled(False)
        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )

        vertical_header = self.verticalHeader()
        vertical_header.setVisible(False)
        vertical_header.setDefaultSectionSize(34)

        header = self.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )

        for column in range(1, 7):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

    def set_results(
        self,
        results: list[PreviewResult],
    ):
        self.setRowCount(len(results))

        for row, result in enumerate(results):
            photo_time = (
                result.photo_time.strftime("%H:%M:%S")
                if result.photo_time
                else "—"
            )

            adjusted_time = (
                result.adjusted_time.strftime("%H:%M:%S")
                if result.adjusted_time
                else "—"
            )

            latitude = (
                f"{result.latitude:.6f}"
                if result.latitude is not None
                else "—"
            )

            longitude = (
                f"{result.longitude:.6f}"
                if result.longitude is not None
                else "—"
            )

            elevation = (
                f"{result.elevation:.1f} m"
                if result.elevation is not None
                else "—"
            )

            status = (
                "Matched"
                if result.matched
                else result.status
            )

            values = [
                result.source_path.name,
                photo_time,
                adjusted_time,
                latitude,
                longitude,
                elevation,
                status,
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)

                if column == 0:
                    item.setToolTip(str(result.source_path))

                if column != 0:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                if column == 6:
                    status_font = item.font()
                    status_font.setBold(True)
                    item.setFont(status_font)

                    if result.matched:
                        item.setForeground(QColor(theme_colors()["accent"]))
                        item.setBackground(QColor(theme_colors()["positive_bg"]))
                    else:
                        item.setForeground(QColor(theme_colors()["negative"]))
                        item.setBackground(QColor(theme_colors()["negative_bg"]))
                    item.setData(Qt.ItemDataRole.UserRole, result.matched)

                self.setItem(
                    row,
                    column,
                    item,
                )

    def refresh_theme(self) -> None:
        colors = theme_colors()
        for row in range(self.rowCount()):
            item = self.item(row, 6)
            if item is None:
                continue
            matched = item.data(Qt.ItemDataRole.UserRole)
            item.setForeground(QColor(colors["accent" if matched else "negative"]))
            item.setBackground(QColor(colors["positive_bg" if matched else "negative_bg"]))
