"""Bar chart component for the JESA DMAT visualization package.

Provides a professional, industrial-grade bar chart built on Plotly's
:class:`go.Bar` trace with support for vertical and horizontal
orientations, grouped and stacked modes, multiple series, value labels,
and Industry-5.0 inspired default styling.

All colors are sourced from :mod:`charts.palette` to maintain visual
consistency across the application.

Usage::

    from charts.bar import BarChart

    chart = BarChart(
        categories=["Q1", "Q2", "Q3", "Q4"],
        values=[65, 72, 78, 85],
        title="Quarterly Progress",
        orientation="vertical",
        mode="grouped",
    )
    fig = chart.create()
    fig.show()

Multi-series example::

    chart = BarChart(
        categories=["Strategy", "Technology", "People"],
        values=[[3.5, 4.2, 2.8], [4.0, 3.8, 3.5]],
        series_names=["Current", "Target"],
        title="Maturity Comparison",
        mode="grouped",
    )
    fig = chart.create()
    fig.show()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

import plotly.graph_objects as go

from charts.palette import (
    BACKGROUND,
    BAR_COLORS,
    BORDER,
    DEFAULT_FONT,
    GRID,
    PRIMARY,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from charts.utils import (
    generate_colors,
    has_negative_values,
    validate_labels,
    validate_numeric_sequence,
    validate_same_length,
)

__all__ = ["BarChart"]

# ---------------------------------------------------------------------------
# Valid orientation and mode literals
# ---------------------------------------------------------------------------
_ORIENTATION_VERTICAL: Literal["vertical"] = "vertical"
_ORIENTATION_HORIZONTAL: Literal["horizontal"] = "horizontal"

_MODE_GROUPED: Literal["grouped"] = "grouped"
_MODE_STACKED: Literal["stacked"] = "stacked"
_MODE_RELATIVE: Literal["relative"] = "relative"

_VALID_ORIENTATIONS: tuple[str, ...] = (
    _ORIENTATION_VERTICAL,
    _ORIENTATION_HORIZONTAL,
)
_VALID_MODES: tuple[str, ...] = (
    _MODE_GROUPED,
    _MODE_STACKED,
    _MODE_RELATIVE,
)

# ---------------------------------------------------------------------------
# Default layout constants
# ---------------------------------------------------------------------------
_DEFAULT_ORIENTATION: str = _ORIENTATION_VERTICAL
_DEFAULT_MODE: str = _MODE_GROUPED
_DEFAULT_SHOW_VALUES: bool = True
_DEFAULT_SHOW_GRID: bool = True
_DEFAULT_SHOW_LEGEND: bool = True
_DEFAULT_SORT: bool = False
_DEFAULT_BAR_COLOR: str = PRIMARY
_DEFAULT_BACKGROUND_COLOR: str = SURFACE
_DEFAULT_PAPER_COLOR: str = BACKGROUND
_DEFAULT_TITLE_COLOR: str = TEXT_PRIMARY
_DEFAULT_FONT_FAMILY: str = DEFAULT_FONT
_DEFAULT_FONT_SIZE: int = 14
_DEFAULT_WIDTH: int = 800
_DEFAULT_HEIGHT: int = 500
_DEFAULT_TEXT_POSITION: str = "outside"
_DEFAULT_TEXT_TEMPLATE: str | None = None
_DEFAULT_HOVER_TEMPLATE: str | None = None


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


def _validate_str_or_none(name: str, value: object) -> None:
    """Raise TypeError if ``value`` is neither a string nor ``None``."""
    if value is not None and not isinstance(value, str):
        raise TypeError(
            f"{name} must be str or None, got {type(value).__name__}"
        )


# =============================================================================
# BarChart
# =============================================================================


@dataclass
class BarChart:
    """Industrial-grade bar chart for comparative data visualisation.

    Supports single or multi-series data, vertical or horizontal
    orientation, grouped or stacked layout, value labels, custom
    colours, and full hover interactivity.

    Call :meth:`create` to obtain the final ``go.Figure``.

    Args:
        categories: Category labels displayed on the category axis.
            Must be non-empty. Duplicates are rejected.
        values: Numeric data to plot.

            * Single-series: ``Sequence[float | int]`` (one bar per category).
            * Multi-series: ``Sequence[Sequence[float | int]]`` where each
              inner sequence is one series.
        series_names: Human-readable names for each series. Required when
            ``values`` is multi-series. Must have the same length as the
            number of series. Defaults to ``None`` for single-series.
        title: Chart title displayed above the figure (default ``""``).
        orientation: Bar direction – ``"vertical"`` (default) or
            ``"horizontal"``.
        mode: Layout mode for multi-series – ``"grouped"`` (default),
            ``"stacked"``, or ``"relative"``.
        colors: Custom bar colours. If ``None``, colours are automatically
            generated from :data:`BAR_COLORS`. Must provide at least as
            many colours as series.
        show_values: If ``True``, display numeric labels on each bar
            (default ``True``).
        text_position: Position of value labels – ``"outside"`` (default),
            ``"inside"``, or ``"auto"``.
        text_template: Plotly text template for value labels (e.g.
            ``"%{y:.1f}"``). If ``None``, raw values are displayed.
        hover_template: Custom Plotly hover template. If ``None``, a
            sensible default is used.
        show_grid: If ``True``, display axis grid lines (default ``True``).
        show_legend: If ``True``, display the legend for multi-series
            charts (default ``True``). Ignored for single-series.
        sort: If ``True``, sort bars by value in descending order
            (default ``False``). Only applied to single-series charts.
        x_axis_title: Title of the horizontal axis (default ``""``).
        y_axis_title: Title of the vertical axis (default ``""``).
        background_color: Plot background colour (default :data:`SURFACE`).
        paper_color: Paper background colour (default :data:`BACKGROUND`).
        font_family: Font family for all text (default :data:`DEFAULT_FONT`).
        font_size: Base font size in pixels (default ``14``). Must be > 0.
        title_color: Colour of the title text (default :data:`TEXT_PRIMARY`).
        width: Figure width in pixels (default ``800``). Must be > 0.
        height: Figure height in pixels (default ``500``). Must be > 0.

    Raises:
        TypeError: If any argument has an invalid type.
        ValueError: If arguments violate business rules (empty data,
            duplicate categories, length mismatch, invalid orientation,
            insufficient colours, etc.).

    Example:
        Single-series::

            >>> chart = BarChart(
            ...     categories=["Q1", "Q2", "Q3", "Q4"],
            ...     values=[65, 72, 78, 85],
            ...     title="Quarterly Progress",
            ... )
            >>> fig = chart.create()

        Multi-series grouped::

            >>> chart = BarChart(
            ...     categories=["A", "B", "C"],
            ...     values=[[10, 20, 15], [12, 18, 22]],
            ...     series_names=["2024", "2025"],
            ...     mode="grouped",
            ...     title="Year-over-Year",
            ... )
            >>> fig = chart.create()
    """

    # -- required data -------------------------------------------------
    categories: Sequence[str]
    values: Sequence[float | int] | Sequence[Sequence[float | int]]

    # -- series metadata -----------------------------------------------
    series_names: Sequence[str] | None = None

    # -- textual metadata ----------------------------------------------
    title: str = ""
    x_axis_title: str = ""
    y_axis_title: str = ""

    # -- visual styling ------------------------------------------------
    orientation: str = _DEFAULT_ORIENTATION
    mode: str = _DEFAULT_MODE
    colors: Sequence[str] | None = None
    show_values: bool = _DEFAULT_SHOW_VALUES
    text_position: str = _DEFAULT_TEXT_POSITION
    text_template: str | None = _DEFAULT_TEXT_TEMPLATE
    hover_template: str | None = _DEFAULT_HOVER_TEMPLATE
    show_grid: bool = _DEFAULT_SHOW_GRID
    show_legend: bool = _DEFAULT_SHOW_LEGEND
    sort: bool = _DEFAULT_SORT

    # -- background & colours ------------------------------------------
    background_color: str = _DEFAULT_BACKGROUND_COLOR
    paper_color: str = _DEFAULT_PAPER_COLOR
    title_color: str = _DEFAULT_TITLE_COLOR

    # -- typography ----------------------------------------------------
    font_family: str = _DEFAULT_FONT_FAMILY
    font_size: int = _DEFAULT_FONT_SIZE

    # -- dimensions ----------------------------------------------------
    width: int = _DEFAULT_WIDTH
    height: int = _DEFAULT_HEIGHT

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self) -> go.Figure:
        """Build and return the configured bar chart figure.

        Returns:
            A Plotly :class:`go.Figure` ready for rendering or export.

        Raises:
            TypeError: If any argument has an invalid type.
            ValueError: If data is inconsistent or violates business rules.
        """
        self._validate()
        traces = self._build_traces()
        fig = go.Figure(data=traces)
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

        # -- duplicate category detection --------------------------------
        seen: set[str] = set()
        for i, cat in enumerate(self.categories):
            if cat in seen:
                raise ValueError(
                    f"Duplicate category detected at index {i}: "
                    f"{cat!r}. Categories must be unique."
                )
            seen.add(cat)

        # -- values type and structure -----------------------------------
        self._validate_values_structure()

        # -- orientation -------------------------------------------------
        _validate_str("orientation", self.orientation)
        if self.orientation not in _VALID_ORIENTATIONS:
            raise ValueError(
                f"orientation must be one of {_VALID_ORIENTATIONS}, "
                f"got {self.orientation!r}"
            )

        # -- mode --------------------------------------------------------
        _validate_str("mode", self.mode)
        if self.mode not in _VALID_MODES:
            raise ValueError(
                f"mode must be one of {_VALID_MODES}, "
                f"got {self.mode!r}"
            )

        # -- text position -----------------------------------------------
        _validate_str("text_position", self.text_position)
        if self.text_position not in ("outside", "inside", "auto"):
            raise ValueError(
                f"text_position must be 'outside', 'inside', or 'auto', "
                f"got {self.text_position!r}"
            )

        # -- string types ------------------------------------------------
        _validate_str("title", self.title)
        _validate_str("x_axis_title", self.x_axis_title)
        _validate_str("y_axis_title", self.y_axis_title)
        _validate_str_or_none("text_template", self.text_template)
        _validate_str_or_none("hover_template", self.hover_template)
        _validate_str("font_family", self.font_family)

        # -- dimensions & font -------------------------------------------
        _validate_positive_int("width", self.width)
        _validate_positive_int("height", self.height)
        _validate_positive_int("font_size", self.font_size)

        # -- boolean types -----------------------------------------------
        if not isinstance(self.show_values, bool):
            raise TypeError(
                f"show_values must be bool, got {type(self.show_values).__name__}"
            )
        if not isinstance(self.show_grid, bool):
            raise TypeError(
                f"show_grid must be bool, got {type(self.show_grid).__name__}"
            )
        if not isinstance(self.show_legend, bool):
            raise TypeError(
                f"show_legend must be bool, got {type(self.show_legend).__name__}"
            )
        if not isinstance(self.sort, bool):
            raise TypeError(
                f"sort must be bool, got {type(self.sort).__name__}"
            )

        # -- colors validation -------------------------------------------
        if self.colors is not None:
            series_count = self._series_count()
            if len(self.colors) < series_count:
                raise ValueError(
                    f"colors must provide at least {series_count} colours "
                    f"for {series_count} series, got {len(self.colors)}"
                )
            for i, color in enumerate(self.colors):
                if not isinstance(color, str):
                    raise TypeError(
                        f"colors[{i}] must be str, got {type(color).__name__}"
                    )

        # -- series_names validation -------------------------------------
        if self.series_names is not None:
            series_count = self._series_count()
            if len(self.series_names) != series_count:
                raise ValueError(
                    f"series_names must have {series_count} entries "
                    f"for {series_count} series, got {len(self.series_names)}"
                )
            for i, name in enumerate(self.series_names):
                if not isinstance(name, str):
                    raise TypeError(
                        f"series_names[{i}] must be str, got {type(name).__name__}"
                    )
                if name.strip() == "":
                    raise ValueError(
                        f"series_names[{i}] must not be an empty or "
                        f"whitespace-only string"
                    )

        # -- stacked mode with negative values ---------------------------
        if self.mode in (_MODE_STACKED, _MODE_RELATIVE):
            for s_idx, series in enumerate(self._normalized_values()):
                if has_negative_values(series):
                    raise ValueError(
                        f"Series {s_idx} contains negative values, which are "
                        f"not supported in '{self.mode}' mode. Use 'grouped' "
                        f"mode or ensure all values are non-negative."
                    )

    def _validate_values_structure(self) -> None:
        """Validate the structure and content of ``values``.

        Determines whether ``values`` represents a single-series or
        multi-series dataset and validates accordingly.

        Raises:
            TypeError: If ``values`` is not a sequence.
            ValueError: If ``values`` is empty or contains invalid data.
        """
        if not isinstance(self.values, Sequence) or isinstance(self.values, (str, bytes)):
            raise TypeError(
                f"values must be a sequence, got {type(self.values).__name__}"
            )

        if len(self.values) == 0:
            raise ValueError("values must not be empty")

        # Detect single-series vs multi-series
        first = self.values[0]
        is_multi = isinstance(first, Sequence) and not isinstance(first, (str, bytes))

        if is_multi:
            # Multi-series: values is Sequence[Sequence[float|int]]
            for s_idx, series in enumerate(self.values):
                if not isinstance(series, Sequence) or isinstance(series, (str, bytes)):
                    raise TypeError(
                        f"values[{s_idx}] must be a sequence of numbers, "
                        f"got {type(series).__name__}"
                    )
                if len(series) == 0:
                    raise ValueError(f"values[{s_idx}] must not be empty")
                validate_numeric_sequence(series, f"values[{s_idx}]")
                validate_same_length(
                    self.categories,
                    series,
                    label_name="categories",
                    value_name=f"values[{s_idx}]",
                )
        else:
            # Single-series: values is Sequence[float|int]
            validate_numeric_sequence(self.values, "values")  # type: ignore[arg-type]
            validate_same_length(
                self.categories,
                self.values,  # type: ignore[arg-type]
                label_name="categories",
                value_name="values",
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_multi_series(self) -> bool:
        """Return ``True`` if the chart has multiple series.

        Returns:
            ``True`` if ``values`` is a sequence of sequences.
        """
        if len(self.values) == 0:
            return False
        first = self.values[0]
        return isinstance(first, Sequence) and not isinstance(first, (str, bytes))

    def _series_count(self) -> int:
        """Return the number of data series.

        Returns:
            ``1`` for single-series, ``len(values)`` for multi-series.
        """
        if self._is_multi_series():
            return len(self.values)
        return 1

    def _normalized_values(self) -> list[list[float | int]]:
        """Normalise ``values`` to a list of series lists.

        Returns:
            List where each element is a series of numeric values.
        """
        if self._is_multi_series():
            return [list(series) for series in self.values]  # type: ignore[arg-type]
        return [list(self.values)]  # type: ignore[arg-type]

    def _normalized_series_names(self) -> list[str]:
        """Return human-readable names for each series.

        If ``series_names`` was provided, returns it. Otherwise generates
        default names.

        Returns:
            List of series names.
        """
        if self.series_names is not None:
            return list(self.series_names)
        count = self._series_count()
        if count == 1:
            return ["Value"]
        return [f"Series {i + 1}" for i in range(count)]

    def _resolve_colors(self) -> list[str]:
        """Resolve the colour palette for all series.

        Uses custom colours if provided, otherwise generates from
        :data:`BAR_COLORS`.

        Returns:
            List of hex colour strings, one per series.
        """
        if self.colors is not None:
            return list(self.colors)[:self._series_count()]
        return generate_colors(BAR_COLORS, self._series_count())

    def _sorted_indices(self) -> list[int]:
        """Return indices that sort single-series data descending.

        Returns:
            List of indices sorted by value in descending order.
        """
        if self._is_multi_series() or not self.sort:
            return list(range(len(self.categories)))
        single_values = list(self.values)  # type: ignore[arg-type]
        return sorted(
            range(len(single_values)),
            key=lambda i: single_values[i],
            reverse=True,
        )

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def _build_traces(self) -> list[go.Bar]:
        """Build the Plotly Bar traces.

        Returns:
            List of configured :class:`go.Bar` traces.
        """
        series_values = self._normalized_values()
        series_names = self._normalized_series_names()
        colors = self._resolve_colors()
        sort_indices = self._sorted_indices()

        # Apply sorting to categories and each series
        sorted_categories = [self.categories[i] for i in sort_indices]
        sorted_series = [
            [series[i] for i in sort_indices]
            for series in series_values
        ]

        traces: list[go.Bar] = []
        is_horizontal = self.orientation == _ORIENTATION_HORIZONTAL

        for s_idx, (series, name, color) in enumerate(
            zip(sorted_series, series_names, colors)
        ):
            text_values = [str(v) for v in series] if self.show_values else None

            trace_kwargs: dict[str, object] = {
                "name": name,
                "marker_color": color,
                "text": text_values,
                "textposition": self.text_position if self.show_values else None,
            }

            if self.text_template is not None:
                trace_kwargs["texttemplate"] = self.text_template

            if self.hover_template is not None:
                trace_kwargs["hovertemplate"] = self.hover_template

            if is_horizontal:
                trace_kwargs["x"] = series
                trace_kwargs["y"] = sorted_categories
                trace_kwargs["orientation"] = "h"
            else:
                trace_kwargs["x"] = sorted_categories
                trace_kwargs["y"] = series

            traces.append(go.Bar(**trace_kwargs))

        return traces

    def _build_layout(self, fig: go.Figure) -> None:
        """Apply bar-chart-specific layout styling to the figure.

        Args:
            fig: The figure to style (mutated in place).
        """
        plotly_modes = {
            _MODE_GROUPED: "group",
            _MODE_STACKED: "stack",
            _MODE_RELATIVE: "relative",
        }
        barmode = plotly_modes[self.mode] if self._is_multi_series() else "group"
        show_legend = self.show_legend and self._is_multi_series()

        grid_color = GRID if self.show_grid else "rgba(0,0,0,0)"

        fig.update_layout(
            width=self.width,
            height=self.height,
            paper_bgcolor=self.paper_color,
            plot_bgcolor=self.background_color,
            barmode=barmode,
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
            showlegend=show_legend,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(
                    family=self.font_family,
                    size=self.font_size - 1,
                    color=TEXT_SECONDARY,
                ),
            ),
            margin=dict(l=60, r=30, t=80, b=80),
        )

        # Axis configuration
        is_horizontal = self.orientation == _ORIENTATION_HORIZONTAL

        if is_horizontal:
            fig.update_xaxes(
                title_text=self.x_axis_title,
                showgrid=self.show_grid,
                gridcolor=grid_color,
                zerolinecolor=BORDER,
                linecolor=GRID,
                tickfont=dict(
                    family=self.font_family,
                    size=self.font_size - 1,
                    color=TEXT_SECONDARY,
                ),
                title_font=dict(
                    family=self.font_family,
                    size=self.font_size,
                    color=TEXT_SECONDARY,
                ),
            )
            fig.update_yaxes(
                title_text=self.y_axis_title,
                showgrid=False,
                zerolinecolor=BORDER,
                linecolor=GRID,
                tickfont=dict(
                    family=self.font_family,
                    size=self.font_size,
                    color=TEXT_SECONDARY,
                ),
                title_font=dict(
                    family=self.font_family,
                    size=self.font_size,
                    color=TEXT_SECONDARY,
                ),
            )
        else:
            fig.update_xaxes(
                title_text=self.x_axis_title,
                showgrid=False,
                zerolinecolor=BORDER,
                linecolor=GRID,
                tickfont=dict(
                    family=self.font_family,
                    size=self.font_size,
                    color=TEXT_SECONDARY,
                ),
                title_font=dict(
                    family=self.font_family,
                    size=self.font_size,
                    color=TEXT_SECONDARY,
                ),
            )
            fig.update_yaxes(
                title_text=self.y_axis_title,
                showgrid=self.show_grid,
                gridcolor=grid_color,
                zerolinecolor=BORDER,
                linecolor=GRID,
                tickfont=dict(
                    family=self.font_family,
                    size=self.font_size - 1,
                    color=TEXT_SECONDARY,
                ),
                title_font=dict(
                    family=self.font_family,
                    size=self.font_size,
                    color=TEXT_SECONDARY,
                ),
            )