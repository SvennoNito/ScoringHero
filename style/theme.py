"""Theme colors shared by Python code (icons, plot chrome). The QSS in modern_theme.qss uses
the same palette; keep them in step."""

import os

ACCENT = "#2f6fed"
TEXT = "#1f2933"
MUTED = "#6b7280"
ICON = "#4b5563"
DISABLED = "#a3aab5"
BORDER = "#d3d8e0"

_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def asset_path(*parts):
    """Absolute path of a bundled file under assets/ (fonts, icons)."""
    return os.path.join(_ASSETS, *parts)

# Channel-name pill on plots: semi-opaque white so the name reads over any trace or image
PILL_BACKGROUND = (255, 255, 255, 215)
