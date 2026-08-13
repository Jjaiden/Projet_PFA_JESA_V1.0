"""Radar chart component for the JESA DMAT visualization package.

Provides a professional, industrial-grade radar (spider) chart built on
Plotly's :class:`go.Scatterpolar` trace. Designed for visualising
multi-dimensional digital maturity assessments with configurable fill,
markers, grid styling, and Industry-5.0 inspired default theming.

All colors are sourced from :mod:`charts.palette` to maintain visual
consistency across the application.

Usage::

    from charts.radar import RadarChart

    chart = RadarChart(
        categories=["Strategy", "Technology", "People", "Process", "Data"],
        values=[3.5, 4.2, 2.8, 4.0, 3.2],
        title="Digital Maturity Assessment",
        fill=True,
    )
    fig = chart.create()
    fig.show()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import plotly.graph_objects as go

from charts.palette import (
    BACKGROUND,
    BORDER,
    GRID,
    PRIMARY,
    RADAR_FILL,
    RADAR_LINE,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from charts.utils import (
    validate_labels,
    validate_numeric_sequence,
    validate_same_length,
)

__all__ = ["RadarChart"]

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
_DEFAULT_FILL: bool = True
_DEFAULT_SHOW_MARKERS: bool = True
_DEFAULT_LINE_WIDTH: int = 2
_DEFAULT_MARKER_SIZE: int = 6
_DEFAULT_RADIAL_GRID_COLOR: str = GRID
_DEFAULT_ANGULAR_GRID_COLOR: str = BORDER
_DEFAULT_BACKGROUND_COLOR: str = SURFACE
_DEFAULT_PAPER_COLOR: str = BACKGROUND
_DEFAULT_TITLE_COLOR: str = TEXT_PRIMARY
_DEFAULT_FONT_FAMILY: str = "Inter"
_DEFAULT_FONT_SIZE: int = 14
_DEFAULT_WIDTH: int = 700
_DEFAULT_HEIGHT: int = 600
_DEFAULT_MIN_VALUE: float = 0.0
_DEFAULT_MAX_VALUE: float | None = None


# ---------------------------------------------------------------------------
# Private validation helpers
# ---------------------------------------------------------------------------


def _validate_positive_int(name: str, value: object) -> None:
    """Raise TypeError/ValueError if ``value`` is not a positive int.

    Args:
        name: Parameter name for error messages.
        value: Value to validate.

    Raises:
        TypeError: If ``value`` is not an ``int`` (bools rejected).
        ValueError: If ``value`` is not strictly positive.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(
            f"{name} must be int, got {type(value).__name__}"
        )
    if value <= 0:
        raise ValueError(f"{name} must be > 0, got {value}")


def _validate_non_negative_int(name: str, value: object) -> None:
    """Raise TypeError/ValueError if ``value`` is not a non-negative int.

    Args:
        name: Parameter name for error messages.
        value: Value to validate.

    Raises:
        TypeError: If ``value`` is not an ``int`` (bools rejected).
        ValueError: If ``value`` is negative.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(
            f"{name} must be int, got {type(value).__name__}"
        )
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")


def _validate_str(name: str, value: object) -> None:
    """
    Raise TypeError if ``value`` is neither a string nor None.

    Args:
        name: Parameter name for error messages.
        value: Value to validate.
    """
    if value is not None and not isinstance(value, str):
        raise TypeError(
            f"{name} must be str or None, got {type(value).__name__}"
        )


# =============================================================================
# RadarChart
# =============================================================================


@dataclass
class RadarChart:
    """Industrial-grade radar chart for multi-dimensional maturity assessment.

    Encapsulates all configuration needed to render a Plotly radar
    (spider) chart. Call :meth:`create` to obtain the final ``go.Figure``.

    The radar requires at least three dimensions (categories) to form a
    meaningful polygon. Values are plotted radially, with each category
    defining one angular axis.

    Args:
        categories: Axis labels displayed around the radar perimeter.
            Must contain at least 3 non-empty strings.
        values: Numeric values corresponding to each category.
            Must have the same length as ``categories``.
        title: Chart title displayed above the figure (default ``""``).
        fill: If ``True``, fill the area inside the radar polygon
            (default ``True``).
        fill_color: Color of the filled area (default :data:`RADAR_FILL`).
        line_color: Color of the radar outline (default :data:`RADAR_LINE`).
        line_width: Width of the radar outline in pixels (default ``2``).
            Must be >= 0.
        show_markers: If ``True``, display markers at each vertex
            (default ``True``).
        marker_size: Diameter of the vertex markers in pixels
            (default ``6``). Must be > 0.
        marker_color: Fill color of the vertex markers
            (default :data:`PRIMARY`).
        min_value: Minimum value of the radial axis (default ``0.0``).
        max_value: Maximum value of the radial axis. If ``None``,
            computed automatically as ``max(values)`` rounded up to the
            nearest integer, with a minimum of ``1.0``.
        radial_grid_color: Color of the concentric grid circles
            (default :data:`GRID`).
        angular_grid_color: Color of the angular axis lines
            (default :data:`BORDER`).
        background_color: Plot background color (default :data:`SURFACE`).
        paper_color: Paper background color (default :data:`BACKGROUND`).
        font_family: Font family for all text (default ``"Inter"``).
        font_size: Base font size in pixels (default ``14``). Must be > 0.
        title_color: Color of the title text (default :data:`TEXT_PRIMARY`).
        width: Figure width in pixels (default ``700``). Must be > 0.
        height: Figure height in pixels (default ``600``). Must be > 0.

    Raises:
        TypeError: If any argument has an invalid type.
        ValueError: If arguments violate business rules (length mismatch,
            insufficient dimensions, out-of-range values, etc.).

    Example:
        >>> chart = RadarChart(
        ...     categories=["Strategy", "Technology", "People", "Process", "Data"],
        ...     values=[3.5, 4.2, 2.8, 4.0, 3.2],
        ...     title="Maturity Profile",
        ...     fill=True,
        ... )
        >>> fig = chart.create()
    """

    # -- required data -------------------------------------------------
    categories: Sequence[str]
    values: Sequence[float | int]

    # -- textual metadata ----------------------------------------------
    title: str = ""

    # -- visual styling ------------------------------------------------
    fill: bool = _DEFAULT_FILL
    fill_color: str = RADAR_FILL
    line_color: str = RADAR_LINE
    line_width: int = _DEFAULT_LINE_WIDTH
    show_markers: bool = _DEFAULT_SHOW_MARKERS
    marker_size: int = _DEFAULT_MARKER_SIZE
    marker_color: str = PRIMARY

    # -- radial axis ---------------------------------------------------
    min_value: float | int = _DEFAULT_MIN_VALUE
    max_value: float | int | None = _DEFAULT_MAX_VALUE

    # -- grid & background ---------------------------------------------
    radial_grid_color: str = _DEFAULT_RADIAL_GRID_COLOR
    angular_grid_color: str = _DEFAULT_ANGULAR_GRID_COLOR
    background_color: str = _DEFAULT_BACKGROUND_COLOR
    paper_color: str = _DEFAULT_PAPER_COLOR

    # -- typography ----------------------------------------------------
    font_family: str = _DEFAULT_FONT_FAMILY
    font_size: int = _DEFAULT_FONT_SIZE
    title_color: str = _DEFAULT_TITLE_COLOR

    # -- dimensions ----------------------------------------------------
    width: int = _DEFAULT_WIDTH
    height: int = _DEFAULT_HEIGHT

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self) -> go.Figure:
        """Build and return the configured radar figure.

        Returns:
            A Plotly :class:`go.Figure` ready for rendering or export.

        Raises:
            TypeError: If any argument has an invalid type.
            ValueError: If values are out of range or dimensions are
                insufficient.
        """
        self._validate()
        trace = self._build_trace()
        fig = go.Figure(data=[trace])
        self._build_layout(fig)
        return fig

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate(self) -> None:
        """Validate all constructor arguments.

        Raises:
            TypeError: If a parameter has an incorrect type.
            ValueError: If a parameter violates business rules.
        """
        # -- categories --------------------------------------------------
        validate_labels(self.categories, "categories")

        # -- minimum dimensions ------------------------------------------
        if len(self.categories) < 3:
            raise ValueError(
                f"categories must contain at least 3 dimensions, "
                f"got {len(self.categories)}"
            )

        # -- values ------------------------------------------------------
        validate_numeric_sequence(self.values, "values")

        # -- length consistency ------------------------------------------
        validate_same_length(
            self.categories,
            self.values,
            label_name="categories",
            value_name="values",
        )

        # -- min / max value types ---------------------------------------
        for name, val in [("min_value", self.min_value)]:
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise TypeError(
                    f"{name} must be a number, got {type(val).__name__}"
                )

        if self.max_value is not None:
            if not isinstance(self.max_value, (int, float)) or isinstance(self.max_value, bool):
                raise TypeError(
                    f"max_value must be a number or None, "
                    f"got {type(self.max_value).__name__}"
                )

        # -- range logic -------------------------------------------------
        resolved_max = self._resolve_max_value()
        if self.min_value >= resolved_max:
            raise ValueError(
                f"min_value ({self.min_value}) must be < max_value "
                f"({resolved_max})"
            )

        # -- values inside range -----------------------------------------
        for i, v in enumerate(self.values):
            if not self.min_value <= v <= resolved_max:
                raise ValueError(
                    f"values[{i}] ({v}) must be between "
                    f"min_value ({self.min_value}) and max_value ({resolved_max})"
                )

        # -- dimensions & font -------------------------------------------
        _validate_positive_int("width", self.width)
        _validate_positive_int("height", self.height)
        _validate_positive_int("font_size", self.font_size)
        _validate_non_negative_int("line_width", self.line_width)
        _validate_positive_int("marker_size", self.marker_size)

        # -- string types ------------------------------------------------
        _validate_str("title", self.title)
        _validate_str("font_family", self.font_family)

        # -- boolean types -----------------------------------------------
        if not isinstance(self.fill, bool):
            raise TypeError(
                f"fill must be bool, got {type(self.fill).__name__}"
            )
        if not isinstance(self.show_markers, bool):
            raise TypeError(
                f"show_markers must be bool, got {type(self.show_markers).__name__}"
            )

    def _resolve_max_value(self) -> float:
        """Return the effective maximum value for the radial axis.

        If ``max_value`` was explicitly provided, returns it.
        Otherwise computes a sensible upper bound from the data.

        Returns:
            Resolved maximum value as a float.
        """
        if self.max_value is not None:
            return float(self.max_value)

        data_max = max(self.values)
        # Round up to the next integer, minimum 1.0
        computed = max(1.0, float(int(data_max) + (1 if data_max > int(data_max) else 0)))
        if computed < data_max:
            computed += 1.0
        return computed

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def _build_trace(self) -> go.Scatterpolar:
        """Build the Plotly Scatterpolar trace.

        Closes the polygon by repeating the first category and value
        at the end of each sequence.

        Returns:
            Configured :class:`go.Scatterpolar`.
        """
        # Close the polygon
        closed_categories = list(self.categories) + [self.categories[0]]
        closed_values = list(self.values) + [self.values[0]]

        fill_mode: str = "toself" if self.fill else "none"

        marker_config: dict[str, object] | None = None
        if self.show_markers:
            marker_config = {
                "size": self.marker_size,
                "color": self.marker_color,
                "line": {"color": self.line_color, "width": 1},
            }

        return go.Scatterpolar(
            r=closed_values,
            theta=closed_categories,
            fill=fill_mode,
            fillcolor=self.fill_color if self.fill else None,
            line={
                "color": self.line_color,
                "width": self.line_width,
            },
            marker=marker_config,
            mode="lines+markers" if self.show_markers else "lines",
            name=self.title if self.title else "Series",
        )

    def _build_layout(self, fig: go.Figure) -> None:
        """Apply radar-specific layout styling to the figure.

        Args:
            fig: The figure to style (mutated in place).
        """
        resolved_max = self._resolve_max_value()

        fig.update_layout(
            width=self.width,
            height=self.height,
            paper_bgcolor=self.paper_color,
            plot_bgcolor=self.background_color,
            font=dict(
                family=self.font_family,
                size=self.font_size,
                color=self.title_color,
            ),
            title={
                "text": self.title,
                "font": {
                    "family": self.font_family,
                    "size": self.font_size + 4,
                    "color": self.title_color,
                },
                "x": 0.5,
                "xanchor": "center",
            } if self.title else None,
            polar=dict(
                bgcolor=self.background_color,
                radialaxis=dict(
                    visible=True,
                    range=[self.min_value, resolved_max],
                    tickfont=dict(
                        family=self.font_family,
                        size=self.font_size - 2,
                        color=TEXT_SECONDARY,
                    ),
                    gridcolor=self.radial_grid_color,
                    linecolor=self.radial_grid_color,
                ),
                angularaxis=dict(
                    tickfont=dict(
                        family=self.font_family,
                        size=self.font_size,
                        color=TEXT_SECONDARY,
                    ),
                    gridcolor=self.angular_grid_color,
                    linecolor=self.angular_grid_color,
                    rotation=90,
                    direction="clockwise",
                ),
            ),
            margin=dict(l=80, r=80, t=80, b=80),
            showlegend=False,
        )