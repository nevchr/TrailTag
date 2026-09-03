from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from ..preview import PreviewResult


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
        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

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

                if column != 0:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                self.setItem(
                    row,
                    column,
                    item,
                )