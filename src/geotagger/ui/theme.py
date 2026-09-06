"""Shared light/dark colors for Qt widgets, painted charts and the map."""

import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication
from ..version import resource_path


THEMES = {
    "light": {
        "window": "#f3f7f5", "surface": "#ffffff", "raised": "#f8fbf9",
        "text": "#18352b", "muted": "#52665b", "border": "#b9cbc2",
        "accent": "#176b4d", "positive_bg": "#e6f6ed",
        "negative": "#9a3d32", "negative_bg": "#fdecea",
        "warning": "#805500", "warning_bg": "#fff3d6",
        "highlight": "#dff1e8", "button": "#edf2ef",
        "chart_fill": "#dcefe5", "chart_line": "#21825f",
    },
    "dark": {
        "window": "#101b17", "surface": "#182820", "raised": "#20342a",
        "text": "#edf7f1", "muted": "#b5c9bd", "border": "#4d6b5b",
        "accent": "#8be0b9", "positive_bg": "#203f30",
        "negative": "#ffb5a9", "negative_bg": "#4b2d2b",
        "warning": "#ffda91", "warning_bg": "#493c23",
        "highlight": "#315542", "button": "#293f32",
        "chart_fill": "#254b38", "chart_line": "#8be0b9",
    },
}


def theme_colors(mode: str | None = None) -> dict[str, str]:
    if mode is None:
        app = QApplication.instance()
        mode = app.property("trailtagTheme") if app else "light"
    return THEMES.get(mode, THEMES["light"])


def apply_theme(app: QApplication, mode: str) -> None:
    colors = theme_colors(mode)
    app.setProperty("trailtagTheme", mode)
    app.styleHints().setColorScheme(
        Qt.ColorScheme.Dark if mode == "dark" else Qt.ColorScheme.Light
    )
    if app.style().objectName().lower() != "fusion":
        app.setStyle("Fusion")
    palette = QPalette()
    roles = {
        "Window": "window", "WindowText": "text", "Base": "surface",
        "AlternateBase": "raised", "Text": "text", "Button": "button",
        "ButtonText": "text", "ToolTipBase": "surface", "ToolTipText": "text",
        "Highlight": "highlight", "HighlightedText": "text",
        "PlaceholderText": "muted", "Link": "accent", "LinkVisited": "muted",
        "Light": "raised", "Midlight": "button", "Mid": "border",
        "Dark": "border", "Shadow": "window", "BrightText": "text",
        "Accent": "accent",
    }
    for role, token in roles.items():
        palette.setColor(getattr(QPalette.ColorRole, role), QColor(colors[token]))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText,
                 QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(colors["muted"]))
    app.setPalette(palette)


def themed_stylesheet(source: str, mode: str) -> str:
    # Keep one layout definition and remap decorative colors. Primary-action
    # text is handled separately from white surfaces to preserve contrast.
    if mode == "dark":
        colors = theme_colors(mode)
        groups = {
            "window": "#f3f7f5",
            "surface": "#ffffff #fbfdfc",
            "raised": "#f8fbf9 #f7faf8 #f1f6f3 #f0f8f4 #eef5f1",
            "button": "#edf2ef #edf1ef #e8edeb",
            "border": "#dce7e1 #cfe0d7 #cfddd6 #c9e7d8 #cfdcd5 #b9cbc2 #e3c4c1 #d7dfdb #79bd9f #b9dfcc",
            "text": "#18352b #143d30 #24483a #29473b #40574d",
            "muted": "#687970 #94a19b #52645b #65766d #52665b",
            "accent": "#176b4d #18704f #27815f #1b7a57 #175b43 #125a40 #2b8a67",
            "positive_bg": "#eaf7f0 #e6f6ed #e6f4ec #e9f6ef",
            "negative": "#9a3d32 #a03333 #c56a61",
            "negative_bg": "#fff3f1 #fdeaea",
            "warning": "#805500", "warning_bg": "#fff3d6",
            "highlight": "#dff1e8",
        }
        replacements = {value: colors[token] for token, values in groups.items()
                        for value in values.split()}
        replacements.update({"#e8f1fb": "#213c50", "#245c91": "#b6dcff"})
        source = re.sub(r"#[0-9a-fA-F]{6}",
                        lambda match: replacements[match.group().lower()], source)
        source += """
        QPushButton#primaryAction { background: #8be0b9; color: #10281e; }
        QPushButton#primaryAction:hover { background: #a4edcc; color: #10281e; }
        QPushButton#primaryAction:disabled, QPushButton#secondaryAction:disabled {
            background: #293f32; color: #b5c9bd; border-color: #4d6b5b;
        }
        QLineEdit, QComboBox, QSpinBox {
            selection-background-color: #315542; selection-color: #edf7f1;
        }
        """
    else:
        source = source.replace("#687970", "#52665b").replace("#94a19b", "#52665b")
    colors = theme_colors(mode)
    up_arrow = resource_path("packaging", f"arrow-up-{mode}.svg").as_posix()
    down_arrow = resource_path("packaging", f"arrow-down-{mode}.svg").as_posix()
    source += f"""
    QProgressBar {{ color: {colors['text']}; }}
    QProgressBar::chunk {{ background: {colors['highlight']}; }}
    QLineEdit, QSpinBox {{ placeholder-text-color: {colors['muted']}; }}
    QSpinBox {{ padding-right: 24px; }}
    QSpinBox::up-button, QSpinBox::down-button {{
        subcontrol-origin: border; width: 22px; border: 0;
        background: {colors['button']};
    }}
    QSpinBox::up-button {{ subcontrol-position: top right; border-top-right-radius: 7px; }}
    QSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 7px; }}
    QSpinBox::up-arrow {{ image: url("{up_arrow}"); width: 12px; height: 8px; }}
    QSpinBox::down-arrow {{ image: url("{down_arrow}"); width: 12px; height: 8px; }}
    QComboBox {{ padding-right: 24px; }}
    QComboBox::drop-down {{ subcontrol-origin: border; subcontrol-position: top right;
        width: 24px; border: 0; }}
    QComboBox::down-arrow {{ image: url("{down_arrow}"); width: 12px; height: 8px; }}
    QMenuBar, QMenu, QDialog, QMessageBox {{
        background: {colors['surface']}; color: {colors['text']};
    }}
    QMenuBar::item:selected, QMenu::item:selected {{
        background: {colors['highlight']}; color: {colors['text']};
    }}
    QComboBox QAbstractItemView {{
        background: {colors['surface']}; color: {colors['text']};
        selection-background-color: {colors['highlight']};
        selection-color: {colors['text']};
    }}
    QToolTip {{ background: {colors['surface']}; color: {colors['text']};
        border: 1px solid {colors['border']}; }}
    """
    return source


def map_stylesheet(mode: str) -> str:
    c = theme_colors(mode)
    return f"""
    html, body {{ color-scheme: {mode}; background: {c['window']}; color: {c['text']}; }}
    .leaflet-container {{ background: {c['raised']}; }}
    .leaflet-popup-content-wrapper, .leaflet-popup-tip, .leaflet-control-attribution,
    .leaflet-bar a {{ background: {c['surface']}; color: {c['text']}; }}
    .leaflet-popup-content, .photo-details, .photo-name {{ color: {c['text']}; }}
    .leaflet-container a, .leaflet-container a.leaflet-popup-close-button {{ color: {c['accent']}; }}
    .leaflet-bar a:hover {{ background: {c['highlight']}; color: {c['text']}; }}
    .preview-unavailable, .preview-loading, .photo-preview {{
        background: {c['raised']}; color: {c['muted']}; }}
    #map-status {{ background: {c['warning_bg']}; color: {c['warning']}; }}
    .empty {{ color: {c['muted']}; }}
    """
