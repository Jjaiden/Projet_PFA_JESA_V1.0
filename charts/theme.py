# JESA_DMAT/charts/theme.py
"""
Central Plotly styling module for the JESA DMAT visualization package.

Provides a professional, industrial-grade Plotly theme built on top of
``plotly_white`` and sourced entirely from :mod:`charts.palette`. Every
colour, font, and spacing constant is defined in a single place.

Public API:

* :data:`TEMPLATE` – a Plotly template encoding the JESA visual identity.
* :func:`apply_theme` – apply the full theme to any figure.
* :func:`export_config` – validated export parameters.

Usage::

    import plotly.graph_objects as go
    from charts.theme import apply_theme

    fig = go.Figure(data=[go.Bar(x=[1,2], y=[3,4])])
    apply_theme(fig)
    fig.show()
"""

from __future__ import annotations

from typing import Final

import plotly.graph_objects as go
import plotly.io as pio

from charts.palette import (
    AXIS,
    BACKGROUND,
    BORDER,
    DEFAULT_FONT,
    GRID,
    HOVER_BACKGROUND,
    LEGEND,
    PRIMARY,
    QUALITATIVE_COLORS,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

__all__ = [
    "TEMPLATE",
    "apply_theme",
    "export_config",
]

# ---------------------------------------------------------------------------
# Valid export formats
# ---------------------------------------------------------------------------
_VALID_EXPORT_FORMATS: Final = frozenset({"png", "svg", "pdf", "jpeg", "webp"})

# ======================================================================
# Typography constants
# ======================================================================
_FONT_FAMILY: Final[str] = DEFAULT_FONT
_FONT_SIZE_TITLE: Final[int] = 18
_FONT_SIZE_AXIS: Final[int] = 12
_FONT_SIZE_LEGEND: Final[int] = 11

# ======================================================================
# Size / export constants
# ======================================================================
_DEFAULT_WIDTH: Final[int] = 800
_DEFAULT_HEIGHT: Final[int] = 450
_DEFAULT_SCALE: Final[float] = 2.0
_DEFAULT_FORMAT: Final[str] = "png"

# ======================================================================
# Plotly template – extends plotly_white with JESA identity
# ======================================================================
_TEMPLATE_BASE: Final = pio.templates["plotly_white"]

TEMPLATE: Final[go.layout.Template] = go.layout.Template()
TEMPLATE.update(_TEMPLATE_BASE)  # inherit all plotly_white defaults

# Font & typography
TEMPLATE.layout.font.family = _FONT_FAMILY
TEMPLATE.layout.font.color = TEXT_PRIMARY
TEMPLATE.layout.font.size = _FONT_SIZE_AXIS

TEMPLATE.layout.title.font.family = _FONT_FAMILY
TEMPLATE.layout.title.font.color = TEXT_PRIMARY
TEMPLATE.layout.title.font.size = _FONT_SIZE_TITLE
TEMPLATE.layout.title.x = 0.5
TEMPLATE.layout.title.xanchor = "center"

# Paper & plot background
TEMPLATE.layout.paper_bgcolor = SURFACE
TEMPLATE.layout.plot_bgcolor = BACKGROUND

# Margins
TEMPLATE.layout.margin.l = 60
TEMPLATE.layout.margin.r = 30
TEMPLATE.layout.margin.t = 60
TEMPLATE.layout.margin.b = 60

# Color sequence
TEMPLATE.layout.colorway = list(QUALITATIVE_COLORS)

# X axis
TEMPLATE.layout.xaxis.gridcolor = GRID
TEMPLATE.layout.xaxis.zerolinecolor = BORDER
TEMPLATE.layout.xaxis.linecolor = AXIS
TEMPLATE.layout.xaxis.title.font.color = TEXT_SECONDARY
TEMPLATE.layout.xaxis.title.font.size = _FONT_SIZE_AXIS
TEMPLATE.layout.xaxis.tickfont.color = TEXT_SECONDARY
TEMPLATE.layout.xaxis.tickfont.size = _FONT_SIZE_AXIS
TEMPLATE.layout.xaxis.automargin = True

# Y axis
TEMPLATE.layout.yaxis.gridcolor = GRID
TEMPLATE.layout.yaxis.zerolinecolor = BORDER
TEMPLATE.layout.yaxis.linecolor = AXIS
TEMPLATE.layout.yaxis.title.font.color = TEXT_SECONDARY
TEMPLATE.layout.yaxis.title.font.size = _FONT_SIZE_AXIS
TEMPLATE.layout.yaxis.tickfont.color = TEXT_SECONDARY
TEMPLATE.layout.yaxis.tickfont.size = _FONT_SIZE_AXIS
TEMPLATE.layout.yaxis.automargin = True

# Legend
TEMPLATE.layout.legend.font.family = _FONT_FAMILY
TEMPLATE.layout.legend.font.color = LEGEND
TEMPLATE.layout.legend.font.size = _FONT_SIZE_LEGEND
TEMPLATE.layout.legend.bgcolor = "rgba(255,255,255,0.6)"
TEMPLATE.layout.legend.bordercolor = BORDER
TEMPLATE.layout.legend.borderwidth = 1
TEMPLATE.layout.legend.orientation = "h"
TEMPLATE.layout.legend.yanchor = "bottom"
TEMPLATE.layout.legend.y = -0.25
TEMPLATE.layout.legend.xanchor = "center"
TEMPLATE.layout.legend.x = 0.5

# Hover
TEMPLATE.layout.hoverlabel.font.family = _FONT_FAMILY
TEMPLATE.layout.hoverlabel.font.size = _FONT_SIZE_AXIS
TEMPLATE.layout.hoverlabel.bgcolor = HOVER_BACKGROUND
TEMPLATE.layout.hoverlabel.bordercolor = PRIMARY


# ======================================================================
# Private helpers
# ======================================================================


def _apply_layout(fig: go.Figure) -> None:
    """Apply the JESA template as the base layout of the figure."""
    fig.update_layout(template=TEMPLATE)


def _apply_axes(fig: go.Figure) -> None:
    """Style x- and y-axes with the JESA grid, line, and tick settings."""
    axis_defaults = dict(
        gridcolor=GRID,
        zerolinecolor=BORDER,
        linecolor=AXIS,
        title_font=dict(color=TEXT_SECONDARY, size=_FONT_SIZE_AXIS),
        tickfont=dict(color=TEXT_SECONDARY, size=_FONT_SIZE_AXIS),
        automargin=True,
    )
    fig.update_xaxes(**axis_defaults)
    fig.update_yaxes(**axis_defaults)


def _apply_legend(fig: go.Figure) -> None:
    """Apply the JESA legend style (horizontal, below the chart)."""
    fig.update_layout(
        legend=dict(
            font=dict(family=_FONT_FAMILY, color=LEGEND, size=_FONT_SIZE_LEGEND),
            bgcolor="rgba(255,255,255,0.6)",
            bordercolor=BORDER,
            borderwidth=1,
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
        )
    )


def _apply_hover(fig: go.Figure) -> None:
    """Style the hover label with the JESA palette."""
    fig.update_layout(
        hoverlabel=dict(
            font=dict(family=_FONT_FAMILY, size=_FONT_SIZE_AXIS),
            bgcolor=HOVER_BACKGROUND,
            bordercolor=PRIMARY,
        )
    )


# ======================================================================
# Public API
# ======================================================================


def apply_theme(fig: go.Figure) -> go.Figure:
    """Apply the full JESA DMAT theme to a Plotly figure.

    Applies the template first, then fine-tunes axes, legend, and hover
    for a consistent industrial look.

    Args:
        fig: A Plotly :class:`go.Figure`.

    Returns:
        The same figure for chaining.

    Raises:
        TypeError: If ``fig`` is not a :class:`go.Figure`.
    """
    if not isinstance(fig, go.Figure):
        raise TypeError(
            f"Expected a plotly Figure, got {type(fig).__name__}"
        )
    _apply_layout(fig)
    _apply_axes(fig)
    _apply_legend(fig)
    _apply_hover(fig)
    return fig


def export_config(
    width: int = _DEFAULT_WIDTH,
    height: int = _DEFAULT_HEIGHT,
    scale: float = _DEFAULT_SCALE,
    format: str = _DEFAULT_FORMAT,
) -> dict[str, object]:
    """Return a validated configuration dictionary for exporting static images.

    Args:
        width: Output width in pixels (must be > 0).
        height: Output height in pixels (must be > 0).
        scale: Scale factor (must be > 0).
        format: Image format – ``"png"``, ``"svg"``, ``"pdf"``, ``"jpeg"``,
            or ``"webp"``.

    Returns:
        Dictionary ready to be unpacked into ``fig.write_image(**config)``.

    Raises:
        ValueError: If any argument is invalid.

    Example:
        >>> config = export_config(width=1200, scale=1.0)
        >>> fig.write_image("chart.png", **config)
    """
    if width <= 0:
        raise ValueError(f"width must be > 0, got {width}")
    if height <= 0:
        raise ValueError(f"height must be > 0, got {height}")
    if scale <= 0:
        raise ValueError(f"scale must be > 0, got {scale}")
    if format not in _VALID_EXPORT_FORMATS:
        raise ValueError(
            f"Unsupported format: {format!r}. "
            f"Allowed: {sorted(_VALID_EXPORT_FORMATS)}"
        )

    return {
        "width": width,
        "height": height,
        "scale": scale,
        "format": format,
    }