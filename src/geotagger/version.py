"""TrailTag release metadata and packaged-resource helpers."""

import sys
from pathlib import Path


__version__ = "0.2.0"


def resource_path(*parts: str) -> Path:
    """Locate a bundled resource in development or in the Windows app."""

    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parents[2]
    return base_path.joinpath(*parts)
