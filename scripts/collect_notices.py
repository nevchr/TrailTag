"""Preserve bundled dependencies' attribution and license information."""

import argparse
import importlib.metadata
import shutil
import sys
from pathlib import Path


PACKAGES = (
    "gpxpy", "piexif", "Pillow", "PySide6", "PySide6_Essentials",
    "PySide6_Addons", "shiboken6", "tzdata", "PyInstaller",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("app_directory", type=Path)
    args = parser.parse_args()
    notices = args.app_directory / "Third-party notices"
    notices.mkdir(parents=True, exist_ok=True)
    summary = [
        "TrailTag third-party software notices",
        "",
        "The following components retain their original licenses and copyrights.",
        "License files supplied by each installed package are preserved below.",
        "These notices do not grant a separate license to TrailTag's own code.",
        "",
    ]
    for name in PACKAGES:
        package = importlib.metadata.distribution(name)
        summary.extend([
            f"{name} {package.version}",
            f"License: {package.metadata.get('License-Expression') or package.metadata.get('License', 'See package notices')}",
            "",
        ])
        for entry in package.files or ():
            relative = Path(str(entry))
            if not relative.parts[0].endswith(".dist-info"):
                continue
            if not any(token in relative.name.lower() for token in ("license", "copying", "notice")):
                continue
            source = Path(package.locate_file(entry))
            if source.is_file():
                destination = notices / name / Path(*relative.parts[1:])
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if python_license.is_file():
        shutil.copy2(python_license, notices / "Python-LICENSE.txt")
    summary.extend([
        "Qt and PySide6 are included as separate, dynamically loaded libraries.",
        "Qt source and module license information: https://code.qt.io/",
        "PySide source: https://code.qt.io/cgit/pyside/pyside-setup.git/",
        "QtWebEngine includes Chromium and other third-party components.",
        "QtWebEngine source/notices: https://code.qt.io/cgit/qt/qtwebengine.git/",
        "",
        "Online map: Leaflet 1.9.4, https://leafletjs.com/ (BSD-2-Clause).",
        "Map data: OpenStreetMap contributors, https://www.openstreetmap.org/copyright.",
        "Leaflet and map tiles are fetched online and are not bundled in TrailTag.",
    ])
    (notices / "README.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
