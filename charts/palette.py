# JESA_DMAT/charts/palette.py
"""
Color palette and helper utilities for the JESA DMAT visualization layer.

Defines the industrial-grade color identity used across all charts,
dashboards, and exports. The palette is built around a deep engineering
blue, cool grays, and status colors suited for professional consulting
environments.

All color constants are module-level (no instantiation needed). Helper
functions provide conversion to ``rgba``, lightening, darkening,
maturity-level lookups, and hex validation.

Usage::

    from charts.palette import PRIMARY, get_maturity_color

    primary = PRIMARY
    level3_color = get_maturity_color(3)
"""

from __future__ import annotations

import colorsys
import re
from collections.abc import Mapping
from typing import Final

__all__ = [
    # Primary colors
    "PRIMARY",
    "PRIMARY_LIGHT",
    "PRIMARY_DARK",
    # Secondary / Accent
    "SECONDARY",
    "ACCENT",
    # Neutrals
    "WHITE",
    "BACKGROUND",
    "SURFACE",
    "TRANSPARENT",
    # Text
    "TEXT_PRIMARY",
    "TEXT_SECONDARY",
    # Borders & Dividers
    "BORDER",
    "DIVIDER",
    # Cards
    "CARD_BACKGROUND",
    "CARD_BORDER",
    "CARD_SHADOW",
    # Status
    "SUCCESS",
    "WARNING",
    "ERROR",
    "INFO",
    # Maturity levels (1–5)
    "LEVEL_1",
    "LEVEL_2",
    "LEVEL_3",
    "LEVEL_4",
    "LEVEL_5",
    # Chart colors
    "RADAR_FILL",
    "RADAR_LINE",
    "GAUGE_BACKGROUND",
    "BAR_PRIMARY",
    "BAR_SECONDARY",
    "ROADMAP_PRIMARY",
    "GRID",
    "AXIS",
    "LEGEND",
    "HOVER_BACKGROUND",
    # Font
    "DEFAULT_FONT",
    # Pre-built sequences
    "RADAR_COLORS",
    "BAR_COLORS",
    "QUALITATIVE_COLORS",
    # Maturity mappings
    "MATURITY_COLORS",
    "MATURITY_LABELS",
    # Helpers
    "is_valid_hex",
    "get_maturity_color",
    "hex_to_rgba",
    "lighten_color",
    "darken_color",
    "is_dark_color",
]

# ---------------------------------------------------------------------------
# Regular expression for a valid 6-digit hex color
# ---------------------------------------------------------------------------
_HEX_RE: Final = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _parse_hex(hex_color: str) -> tuple[int, int, int]:
    """Validate and parse a hex color into (R, G, B) integers."""
    if not _HEX_RE.match(hex_color):
        raise ValueError(
            f"Invalid hex color: {hex_color!r}. Expected format '#RRGGBB'."
        )
    return (
        int(hex_color[1:3], 16),
        int(hex_color[3:5], 16),
        int(hex_color[5:7], 16),
    )


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    """Convert (R, G, B) floats in [0,1] back to a hex string."""
    return f"#{int(round(r * 255)):02X}{int(round(g * 255)):02X}{int(round(b * 255)):02X}"


# ======================================================================
# Primary colors
# ======================================================================
PRIMARY: Final[str] = "#1E3A8A"
PRIMARY_LIGHT: Final[str] = "#2563EB"
PRIMARY_DARK: Final[str] = "#1E40AF"

# ======================================================================
# Secondary / Accent
# ======================================================================
SECONDARY: Final[str] = "#3B82F6"
ACCENT: Final[str] = "#60A5FA"

# ======================================================================
# Neutrals
# ======================================================================
WHITE: Final[str] = "#FFFFFF"
BACKGROUND: Final[str] = "#F5F7FA"
SURFACE: Final[str] = "#FFFFFF"
TRANSPARENT: Final[str] = "rgba(0,0,0,0)"

# ======================================================================
# Text
# ======================================================================
TEXT_PRIMARY: Final[str] = "#0F172A"
TEXT_SECONDARY: Final[str] = "#475569"

# ======================================================================
# Borders & Dividers
# ======================================================================
BORDER: Final[str] = "#E2E8F0"
DIVIDER: Final[str] = "#CBD5E1"

# ======================================================================
# Cards
# ======================================================================
CARD_BACKGROUND: Final[str] = "#FFFFFF"
CARD_BORDER: Final[str] = "#E2E8F0"
CARD_SHADOW: Final[str] = "rgba(15, 23, 42, 0.08)"

# ======================================================================
# Status
# ======================================================================
SUCCESS: Final[str] = "#10B981"
WARNING: Final[str] = "#F59E0B"
ERROR: Final[str] = "#EF4444"
INFO: Final[str] = "#3B82F6"

# ======================================================================
# Maturity levels (1–5)
# ======================================================================
LEVEL_1: Final[str] = "#EF4444"   # Red – Initial
LEVEL_2: Final[str] = "#F97316"   # Orange – Managed
LEVEL_3: Final[str] = "#EAB308"   # Yellow – Defined
LEVEL_4: Final[str] = "#3B82F6"   # Blue – Integrated
LEVEL_5: Final[str] = "#10B981"   # Green – Optimised

# ======================================================================
# Chart-specific colors
# ======================================================================
RADAR_FILL: Final[str] = "rgba(37, 99, 235, 0.15)"
RADAR_LINE: Final[str] = "#2563EB"
GAUGE_BACKGROUND: Final[str] = "#E2E8F0"
BAR_PRIMARY: Final[str] = "#2563EB"
BAR_SECONDARY: Final[str] = "#93C5FD"
ROADMAP_PRIMARY: Final[str] = "#1E3A8A"

# ======================================================================
# Dashboard / Layout
# ======================================================================
GRID: Final[str] = "#E2E8F0"
AXIS: Final[str] = "#94A3B8"
LEGEND: Final[str] = "#64748B"
HOVER_BACKGROUND: Final[str] = "#EFF6FF"

# ======================================================================
# Typography
# ======================================================================
DEFAULT_FONT: Final[str] = "Inter"

# ======================================================================
# Pre-built color sequences
# ======================================================================
RADAR_COLORS: Final[tuple[str, ...]] = (
    "#2563EB",
    "#3B82F6",
    "#60A5FA",
    "#93C5FD",
    "#BFDBFE",
)
"""Default color sequence for radar / spider chart series."""

BAR_COLORS: Final[tuple[str, ...]] = (
    "#1E3A8A",
    "#2563EB",
    "#3B82F6",
    "#60A5FA",
    "#93C5FD",
)
"""Default color sequence for bar chart categories."""

QUALITATIVE_COLORS: Final[tuple[str, ...]] = (
    "#2563EB",
    "#10B981",
    "#F59E0B",
    "#EF4444",
    "#8B5CF6",
    "#14B8A6",
)
"""Qualitative palette for categorical data (up to 6 categories)."""

# ======================================================================
# Maturity mappings
# ======================================================================
MATURITY_COLORS: Final[Mapping[int, str]] = {
    1: LEVEL_1,
    2: LEVEL_2,
    3: LEVEL_3,
    4: LEVEL_4,
    5: LEVEL_5,
}
"""Mapping from maturity level (1–5) to its associated hex color."""

MATURITY_LABELS: Final[Mapping[int, str]] = {
    1: "Initial",
    2: "Managed",
    3: "Defined",
    4: "Integrated",
    5: "Optimised",
}
"""Human-readable labels for each maturity level."""


# ======================================================================
# Public helpers
# ======================================================================


def is_valid_hex(hex_color: str) -> bool:
    """Check whether a string is a valid ``#RRGGBB`` hex color.

    Args:
        hex_color: The string to validate.

    Returns:
        ``True`` if the format is correct, ``False`` otherwise.
    """
    return bool(_HEX_RE.match(hex_color))


def get_maturity_color(level: int) -> str:
    """Return the hex color for a given maturity level.

    Args:
        level: Maturity level, must be an integer between 1 and 5 inclusive.

    Returns:
        Hex color string (e.g. ``"#10B981"``).

    Raises:
        ValueError: If ``level`` is outside the 1–5 range.
    """
    if level not in MATURITY_COLORS:
        raise ValueError(
            f"Invalid maturity level: {level}. Must be 1–5."
        )
    return MATURITY_COLORS[level]


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert a hex color to an ``rgba()`` CSS string.

    Args:
        hex_color: A ``#RRGGBB`` color string.
        alpha: Opacity value between ``0.0`` (fully transparent) and
            ``1.0`` (fully opaque). Defaults to ``1.0``.

    Returns:
        CSS ``rgba(r, g, b, a)`` string.

    Raises:
        ValueError: If the hex string is invalid or ``alpha`` is out of range.
    """
    if not 0.0 <= alpha <= 1.0:
        raise ValueError(
            f"Alpha must be between 0.0 and 1.0, got {alpha}."
        )
    r, g, b = _parse_hex(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha})"


def lighten_color(hex_color: str, amount: float = 0.2) -> str:
    """Return a lighter version of a hex color.

    Args:
        hex_color: A ``#RRGGBB`` color string.
        amount: How much to increase lightness (0.0 = no change, 1.0 = white).

    Returns:
        New ``#RRGGBB`` hex color.

    Raises:
        ValueError: If the hex format is invalid or ``amount`` is out of range.
    """
    if not 0.0 <= amount <= 1.0:
        raise ValueError(
            f"amount must be between 0.0 and 1.0, got {amount}."
        )
    r, g, b = _parse_hex(hex_color)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    l = min(1.0, l + (1.0 - l) * amount)
    nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
    return _rgb_to_hex(nr, ng, nb)


def darken_color(hex_color: str, amount: float = 0.2) -> str:
    """Return a darker version of a hex color.

    Args:
        hex_color: A ``#RRGGBB`` color string.
        amount: How much to decrease lightness (0.0 = no change, 1.0 = black).

    Returns:
        New ``#RRGGBB`` hex color.

    Raises:
        ValueError: If the hex format is invalid or ``amount`` is out of range.
    """
    if not 0.0 <= amount <= 1.0:
        raise ValueError(
            f"amount must be between 0.0 and 1.0, got {amount}."
        )
    r, g, b = _parse_hex(hex_color)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    l = max(0.0, l * (1.0 - amount))
    nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
    return _rgb_to_hex(nr, ng, nb)


def is_dark_color(hex_color: str) -> bool:
    """Determine whether a hex color is perceived as dark.

    Uses the relative luminance formula (WCAG). Returns ``True`` for
    dark colors (where white text would contrast well), ``False`` for
    light colors.

    Args:
        hex_color: A ``#RRGGBB`` color string.

    Returns:
        ``True`` if the color is dark, ``False`` otherwise.

    Raises:
        ValueError: If the hex format is invalid.

    Example:
        >>> is_dark_color("#1E3A8A")
        True
        >>> is_dark_color("#FFFFFF")
        False
    """
    r, g, b = _parse_hex(hex_color)
    luminance = 0.2126 * (r / 255) + 0.7152 * (g / 255) + 0.0722 * (b / 255)
    return luminance < 0.5