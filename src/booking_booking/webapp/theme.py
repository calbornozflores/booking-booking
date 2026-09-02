"""Design tokens shared across personal projects - see
~/code/personal/DESIGN_SYSTEM.md.

Streamlit's own theme (.streamlit/config.toml's [theme] table) covers most
of the standard natively and needs no Python constants. This module exists
only for the rare spot Streamlit's theme can't reach - e.g. a
pandas.Styler-highlighted dataframe row, which renders raw inline CSS the
theme engine doesn't touch.

Keep these values in sync with .streamlit/config.toml by hand: Streamlit
reads that TOML file directly at startup and can't be configured from
Python constants, so the same numbers necessarily live in both places.
"""

BG = "#0f0f1a"
SURFACE = "#1a1a2e"
SURFACE_2 = "#16213e"
BORDER = "#2a2a4a"
ACCENT = "#6c63ff"
ACCENT_HOVER = "#8b85ff"
ACCENT_GRADIENT_END = "#a78bfa"
GREEN = "#22c55e"
YELLOW = "#f59e0b"
RED = "#ef4444"
TEXT = "#e2e8f0"
TEXT_MUTED = "#94a3b8"

RADIUS = "12px"
RADIUS_PILL = "999px"
RADIUS_SM = "8px"
SHADOW = "0 4px 24px rgba(0,0,0,0.4)"


def tint(hex_color: str, bg_opacity: float = 0.15) -> str:
    """rgba() tint at the standard's pill-badge opacity (~15% bg)."""
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return f"rgba({r}, {g}, {b}, {bg_opacity})"
