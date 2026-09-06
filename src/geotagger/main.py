import sys
from pathlib import Path

from .version import __version__, resource_path
from .windows_integration import configure_windows_identity


def main(
    smoke_test: bool = False,
    smoke_status_path: Path | None = None,
) -> int:
    def mark(stage: str) -> None:
        if smoke_status_path is not None:
            smoke_status_path.write_text(stage, encoding="utf-8")

    mark("main-entered")

    from PySide6.QtCore import QSettings
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    mark("widgets-imported")

    from .ui.main_window import MainWindow
    from .trip_store import TripStore

    mark("window-module-imported")

    app_arguments = [
        argument
        for argument in sys.argv
        if argument != "--smoke-test"
        and not argument.startswith("--smoke-test-status=")
    ]

    configure_windows_identity()
    app = QApplication(app_arguments)
    app.setApplicationName("TrailTag")
    app.setApplicationDisplayName("TrailTag")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("TrailTag")

    icon_path = resource_path("packaging", "trailtag.ico")
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))

    mark("application-created")

    smoke_settings_path = None
    if smoke_test and smoke_status_path is not None:
        smoke_settings_path = smoke_status_path.with_suffix(".ini")
        settings = QSettings(
            str(smoke_settings_path),
            QSettings.Format.IniFormat,
        )
        window = MainWindow(
            trip_store=TripStore(smoke_status_path.with_suffix(".trips.json")),
            settings=settings,
        )
    else:
        window = MainWindow()

    mark("window-created")

    if smoke_test:
        if window.windowTitle() != "TrailTag":
            raise RuntimeError(
                "The packaged window did not initialize correctly."
            )

        window.close()
        if smoke_settings_path is not None:
            smoke_settings_path.unlink(missing_ok=True)
        return 0

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
