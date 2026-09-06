"""PyInstaller-friendly entry point for TrailTag."""

import os
import sys
from pathlib import Path


SMOKE_TEST_FLAG = "--smoke-test"
SMOKE_STATUS_PREFIX = "--smoke-test-status="
SMOKE_STATUS_ARGUMENT = next(
    (
        argument
        for argument in sys.argv
        if argument.startswith(SMOKE_STATUS_PREFIX)
    ),
    None,
)
SMOKE_TEST = SMOKE_TEST_FLAG in sys.argv or SMOKE_STATUS_ARGUMENT is not None
SMOKE_STATUS_PATH = None

if SMOKE_TEST:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    SMOKE_STATUS_PATH = (
        Path(SMOKE_STATUS_ARGUMENT[len(SMOKE_STATUS_PREFIX):])
        if SMOKE_STATUS_ARGUMENT is not None
        else Path(sys.executable).with_name("TrailTag-smoke-test.txt")
    )
    SMOKE_STATUS_PATH.write_text("launcher-started", encoding="utf-8")


# Keep Windows pointed at the Qt DLLs shipped beside the frozen app. This is
# needed before importing PySide when another Qt installation is discoverable
# elsewhere on the machine.
_DLL_DIRECTORY_HANDLES = []
if getattr(sys, "frozen", False) and sys.platform == "win32":
    import ctypes

    internal_directory = Path(sys._MEIPASS)
    qt_directory = internal_directory / "PySide6"
    shiboken_directory = internal_directory / "shiboken6"

    for directory in (qt_directory, shiboken_directory):
        _DLL_DIRECTORY_HANDLES.append(
            os.add_dll_directory(str(directory))
        )

    for library_name in (
        "Qt6Core.dll",
        "Qt6Gui.dll",
        "Qt6Widgets.dll",
    ):
        ctypes.WinDLL(str(qt_directory / library_name))

from src.geotagger.main import main

if SMOKE_STATUS_PATH is not None:
    SMOKE_STATUS_PATH.write_text("imports-complete", encoding="utf-8")


if __name__ == "__main__":
    exit_code = main(
        smoke_test=SMOKE_TEST,
        smoke_status_path=SMOKE_STATUS_PATH,
    )

    if SMOKE_TEST:
        SMOKE_STATUS_PATH.write_text("passed", encoding="utf-8")

        # Qt WebEngine may keep helper threads alive when a frozen app
        # exits immediately after construction. The smoke test has
        # completed at this point, so terminate the test process cleanly.
        os._exit(exit_code)

    raise SystemExit(exit_code)
