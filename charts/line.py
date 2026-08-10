"""Line chart component for the JESA DMAT visualization package.

Provides a professional, industrial-grade line chart built on Plotly's
:class:`go.Scatter` trace with support for single and multiple series,
configurable markers, smoothing (spline interpolation), filled areas,
custom line styles, annotations, and Industry-5.0 inspired default styling.

The component is architected to support a secondary Y-axis in future
iterations without breaking the public API.

All colors are sourced from :mod:`charts.palette` to maintain visual
consistency across the application.

Usage::

    from charts.line import LineChart

    chart = LineChart(
        x=["Jan", "Feb", "Mar", "Apr", "May"],
        y=[120, 135, 128, 142, 155],
        title="Monthly Progress",
        show_markers=True,
        smooth=True,
    )
    fig = chart.create()
    fig.show()

Multi-series example::

    chart = LineChart(
        x=["Q1", "Q2", "Q3", "Q4"],
        y=[[65, 72, 78, 85], [60, 70, 75, 88]],
        series_names=["2024", "2025"],
        title="Year-over-Year Comparison",
        fill_area=True,
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
    BORDER,
    DEFAULT_FONT,
    GRID,
    PRIMARY,
    QUALITATIVE_COLORS,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from charts.utils import (
    generate_colors,
    validate_labels,
    validate_numeric_sequence,
    validate_same_length,
)

__all__ = ["LineChart"]

# ---------------------------------------------------------------------------
# Valid line style literals
# ---------------------------------------------------------------------------
_LINE_STYLE_SOLID: Literal["solid"] = "solid"
_LINE_STYLE_DASH: Literal["dash"] = "dash"
_LINE_STYLE_DOT: Literal["dot"] = "dot"
_LINE_STYLE_DASHDOT: Literal["dashdot"] = "dashdot"

_VALID_LINE_STYLES: tuple[str, ...] = (
    _LINE_STYLE_SOLID,
    _LINE_STYLE_DASH,
    _LINE_STYLE_DOT,
    _LINE_STYLE_DASHDOT,
)

# ---------------------------------------------------------------------------
# Default layout constants
# ---------------------------------------------------------------------------
_DEFAULT_SHOW_MARKERS: bool = True
_DEFAULT_MARKER_SIZE: int = 6
_DEFAULT_LINE_WIDTH: int = 2
_DEFAULT_LINE_STYLE: str = _LINE_STYLE_SOLID
_DEFAULT_SMOOTH: bool = False
_DEFAULT_FILL_AREA: bool = False
_DEFAULT_FILL_OPACITY: float = 0.15
_DEFAULT_SHOW_GRID: bool = True
_DEFAULT_SHOW_LEGEND: bool = True
_DEFAULT_BACKGROUND_COLOR: str = SURFACE
_DEFAULT_PAPER_COLOR: str = BACKGROUND
_DEFAULT_TITLE_COLOR: str = TEXT_PRIMARY
_DEFAULT_FONT_FAMILY: str = DEFAULT_FONT
_DEFAULT_FONT_SIZE: int = 14
_DEFAULT_WIDTH: int = 900
_DEFAULT_HEIGHT: int = 500
_DEFAULT_HOVER_TEMPLATE: str | None = None
_DEFAULT_SECONDARY_Y: bool = False


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
    """Raise TypeError if ``value`` is not a string."""
    if not isinstance(value, str):
        raise TypeError(
            f"{name} must be str, got {type(value).__name__}"
        )


def _validate_str_or_none(name: str, value: object) -> None:
    """Raise TypeError if ``value`` is neither a string nor ``None``."""
    if value is not None and not isinstance(value, str):
        raise TypeError(
            f"{name} must be str or None, got {type(value).__name__}"
        )


def _validate_opacity(name: str, value: float) -> None:
    """Raise ValueError if ``value`` is not in ``[0.0, 1.0]``.

    Args:
        name: Parameter name for error messages.
        value: Opacity value to validate.

    Raises:
        TypeError: If ``value`` is not a number.
        ValueError: If ``value`` is outside the ``[0.0, 1.0]`` range.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(
            f"{name} must be a number, got {type(value).__name__}"
        )
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError(
            f"{name} must be between 0.0 and 1.0, got {value}"
        )


# =============================================================================
# LineChart
# =============================================================================


@dataclass
class LineChart:
    """Industrial-grade line chart for time-series and trend visualisation.

    Supports single or multi-series data, configurable markers, spline
    smoothing, filled areas under curves, custom line styles, and
    annotations. Architected with secondary Y-axis support for future
    extensibility.

    Call :meth:`create` to obtain the final ``go.Figure``.

    Args:
        x: Category or time labels displayed on the horizontal axis.
            Must be non-empty. Duplicates are rejected.
        y: Numeric data to plot.

            * Single-series: ``Sequence[float | int]`` (one point per x).
            * Multi-series: ``Sequence[Sequence[float | int]]`` where each
              inner sequence is one series aligned with ``x``.
        series_names: Optional human-readable names for each series. When
            omitted, default names are generated. If provided, it must have
            the same length as the number of series.
        title: Chart title displayed above the figure (default ``""``).
        x_axis_title: Title of the horizontal axis (default ``""``).
        y_axis_title: Title of the primary vertical axis (default ``""``).
        show_markers: If ``True``, display circular markers at each data
            point (default ``True``).
        marker_size: Diameter of the markers in pixels (default ``6``).
            Must be > 0.
        marker_color: Fill colour of the markers. If ``None``, uses the
            series line colour (default ``None``).
        line_width: Width of the line strokes in pixels (default ``2``).
            Must be >= 0.
        line_style: Dash style of the lines – ``"solid"`` (default),
            ``"dash"``, ``"dot"``, or ``"dashdot"``.
        line_colors: Custom line colours. If ``None``, colours are
            automatically generated from :data:`QUALITATIVE_COLORS`.
            Must provide at least as many colours as series.
        smooth: If ``True``, render lines as Catmull-Rom splines instead
            of straight segments (default ``False``).
        fill_area: If ``True``, fill the area between each line and the
            x-axis with a semi-transparent colour (default ``False``).
        fill_color: Explicit fill colour. If ``None`` and ``fill_area`` is
            ``True``, the fill colour is derived from the line colour with
            ``fill_opacity`` (default ``None``).
        fill_opacity: Opacity of the filled area when ``fill_area`` is
            ``True`` and no explicit ``fill_color`` is provided
            (default ``0.15``). Must be in ``[0.0, 1.0]``.
        show_grid: If ``True``, display axis grid lines (default ``True``).
        show_legend: If ``True``, display the legend for multi-series
            charts (default ``True``). Ignored for single-series.
        hover_template: Custom Plotly hover template. If ``None``, a
            sensible default is used.
        annotations: Optional sequence of annotation dictionaries forwarded
            directly to Plotly. Each dict must contain at least ``x`` and
            ``text`` keys (default ``None``).
        secondary_y: Reserved for future use. When ``True``, the figure
            layout is prepared to host a secondary Y-axis (default ``False``).
        background_color: Plot background colour (default :data:`SURFACE`).
        paper_color: Paper background colour (default :data:`BACKGROUND`).
        title_color: Colour of the title text (default :data:`TEXT_PRIMARY`).
        font_family: Font family for all text (default :data:`DEFAULT_FONT`).
        font_size: Base font size in pixels (default ``14``). Must be > 0.
        width: Figure width in pixels (default ``900``). Must be > 0.
        height: Figure height in pixels (default ``500``). Must be > 0.

    Raises:
        TypeError: If any argument has an invalid type.
        ValueError: If arguments violate business rules (empty data,
            duplicate x labels, length mismatch, invalid line style,
            insufficient colours, etc.).

    Example:
        Single-series with smoothing::

            >>> chart = LineChart(
            ...     x=["W1", "W2", "W3", "W4"],
            ...     y=[45, 52, 48, 61],
            ...     title="Weekly Velocity",
            ...     smooth=True,
            ...     fill_area=True,
            ... )
            >>> fig = chart.create()

        Multi-series with markers::

            >>> chart = LineChart(
            ...     x=["M1", "M2", "M3"],
            ...     y=[[10, 15, 12], [8, 14, 18]],
            ...     series_names=["Team A", "Team B"],
            ...     show_markers=True,
            ...     marker_size=8,
            ... )
            >>> fig = chart.create()
    """

    # -- required data -------------------------------------------------
    x: Sequence[str]
    y: Sequence[float | int] | Sequence[Sequence[float | int]]

    # -- series metadata -----------------------------------------------
    series_names: Sequence[str] | None = None

    # -- textual metadata ----------------------------------------------
    title: str = ""
    x_axis_title: str = ""
    y_axis_title: str = ""

    # -- visual styling ------------------------------------------------
    show_markers: bool = _DEFAULT_SHOW_MARKERS
    marker_size: int = _DEFAULT_MARKER_SIZE
    marker_color: str | None = None
    line_width: int = _DEFAULT_LINE_WIDTH
    line_style: str = _DEFAULT_LINE_STYLE
    line_colors: Sequence[str] | None = None
    smooth: bool = _DEFAULT_SMOOTH
    fill_area: bool = _DEFAULT_FILL_AREA
    fill_color: str | None = None
    fill_opacity: float = _DEFAULT_FILL_OPACITY

    # -- interactivity -------------------------------------------------
    show_grid: bool = _DEFAULT_SHOW_GRID
    show_legend: bool = _DEFAULT_SHOW_LEGEND
    hover_template: str | None = _DEFAULT_HOVER_TEMPLATE
    annotations: Sequence[dict[str, object]] | None = None

    # -- future-ready architecture -------------------------------------
    secondary_y: bool = _DEFAULT_SECONDARY_Y

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
        """Build and return the configured line chart figure.

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
        self._build_axes(fig)
        self._build_hover(fig)
        self._build_annotations(fig)
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
        # -- x labels ----------------------------------------------------
        validate_labels(self.x, "x")

        # -- duplicate x detection ---------------------------------------
        seen: set[str] = set()
        for i, label in enumerate(self.x):
            if label in seen:
                raise ValueError(
                    f"Duplicate x label detected at index {i}: "
                    f"{label!r}. x labels must be unique."
                )
            seen.add(label)

        # -- y values structure ------------------------------------------
        self._validate_y_structure()

        if self.secondary_y and not self._is_multi_series():
            raise ValueError("secondary_y requires at least two data series")

        # -- line style --------------------------------------------------
        _validate_str("line_style", self.line_style)
        if self.line_style not in _VALID_LINE_STYLES:
            raise ValueError(
                f"line_style must be one of {_VALID_LINE_STYLES}, "
                f"got {self.line_style!r}"
            )

        # -- dimensions & font -------------------------------------------
        _validate_positive_int("width", self.width)
        _validate_positive_int("height", self.height)
        _validate_positive_int("font_size", self.font_size)
        _validate_positive_int("marker_size", self.marker_size)
        _validate_non_negative_int("line_width", self.line_width)

        # -- opacity -----------------------------------------------------
        _validate_opacity("fill_opacity", self.fill_opacity)

        # -- string types ------------------------------------------------
        _validate_str("title", self.title)
        _validate_str("x_axis_title", self.x_axis_title)
        _validate_str("y_axis_title", self.y_axis_title)
        _validate_str_or_none("hover_template", self.hover_template)
        _validate_str("font_family", self.font_family)

        if self.marker_color is not None:
            _validate_str("marker_color", self.marker_color)
        if self.fill_color is not None:
            _validate_str("fill_color", self.fill_color)

        # -- boolean types -----------------------------------------------
        for name in ("show_markers", "smooth", "fill_area", "show_grid",
                     "show_legend", "secondary_y"):
            val = getattr(self, name)
            if not isinstance(val, bool):
                raise TypeError(
                    f"{name} must be bool, got {type(val).__name__}"
                )

        # -- line colors validation --------------------------------------
        if self.line_colors is not None:
            if isinstance(self.line_colors, (str, bytes)):
                raise TypeError("line_colors must be a sequence of colour strings, not a string")
            series_count = self._series_count()
            if len(self.line_colors) < series_count:
                raise ValueError(
                    f"line_colors must provide at least {series_count} colours "
                    f"for {series_count} series, got {len(self.line_colors)}"
                )
            for i, color in enumerate(self.line_colors):
                if not isinstance(color, str):
                    raise TypeError(
                        f"line_colors[{i}] must be str, got {type(color).__name__}"
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

        # -- annotations validation --------------------------------------
        if self.annotations is not None:
            if not isinstance(self.annotations, Sequence):
                raise TypeError(
                    f"annotations must be a sequence, got {type(self.annotations).__name__}"
                )
            for i, ann in enumerate(self.annotations):
                if not isinstance(ann, dict):
                    raise TypeError(
                        f"annotations[{i}] must be dict, got {type(ann).__name__}"
                    )
                missing = {"x", "text"} - ann.keys()
                if missing:
                    raise ValueError(
                        f"annotations[{i}] is missing required keys: {sorted(missing)}"
                    )

    def _validate_y_structure(self) -> None:
        """Validate the structure and content of ``y``.

        Determines whether ``y`` represents a single-series or
        multi-series dataset and validates accordingly.

        Raises:
            TypeError: If ``y`` is not a sequence.
            ValueError: If ``y`` is empty or contains invalid data.
        """
        if not isinstance(self.y, Sequence) or isinstance(self.y, (str, bytes)):
            raise TypeError(
                f"y must be a sequence, got {type(self.y).__name__}"
            )

        if len(self.y) == 0:
            raise ValueError("y must not be empty")

        first = self.y[0]
        is_multi = isinstance(first, Sequence) and not isinstance(first, (str, bytes))

        if is_multi:
            for s_idx, series in enumerate(self.y):
                if not isinstance(series, Sequence) or isinstance(series, (str, bytes)):
                    raise TypeError(
                        f"y[{s_idx}] must be a sequence of numbers, "
                        f"got {type(series).__name__}"
                    )
                if len(series) == 0:
                    raise ValueError(f"y[{s_idx}] must not be empty")
                validate_numeric_sequence(series, f"y[{s_idx}]")
                validate_same_length(
                    self.x,
                    series,
                    label_name="x",
                    value_name=f"y[{s_idx}]",
                )
        else:
            validate_numeric_sequence(self.y, "y")  # type: ignore[arg-type]
            validate_same_length(
                self.x,
                self.y,  # type: ignore[arg-type]
                label_name="x",
                value_name="y",
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_multi_series(self) -> bool:
        """Return ``True`` if the chart has multiple series.

        Returns:
            ``True`` if ``y`` is a sequence of sequences.
        """
        if len(self.y) == 0:
            return False
        first = self.y[0]
        return isinstance(first, Sequence) and not isinstance(first, (str, bytes))

    def _series_count(self) -> int:
        """Return the number of data series.

        Returns:
            ``1`` for single-series, ``len(y)`` for multi-series.
        """
        if self._is_multi_series():
            return len(self.y)
        return 1

    def _normalized_y(self) -> list[list[float | int]]:
        """Normalise ``y`` to a list of series lists.

        Returns:
            List where each element is a series of numeric values.
        """
        if self._is_multi_series():
            return [list(series) for series in self.y]  # type: ignore[arg-type]
        return [list(self.y)]  # type: ignore[arg-type]

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

    def _resolve_line_colors(self) -> list[str]:
        """Resolve the line colour palette for all series.

        Uses custom colours if provided, otherwise generates from
        :data:`QUALITATIVE_COLORS`.

        Returns:
            List of hex colour strings, one per series.
        """
        if self.line_colors is not None:
            return list(self.line_colors)[:self._series_count()]
        return generate_colors(QUALITATIVE_COLORS, self._series_count())

    def _resolve_fill_color(self, line_color: str) -> str:
        """Resolve the fill colour for a given line colour.

        If an explicit ``fill_color`` was provided, returns it.
        Otherwise derives a semi-transparent colour from the line colour
        using ``fill_opacity``.

        Args:
            line_color: The line colour to derive from.

        Returns:
            CSS colour string for the fill area.
        """
        if self.fill_color is not None:
            return self.fill_color
        # Convert hex to rgba with opacity
        if line_color.startswith("#") and len(line_color) == 7:
            r = int(line_color[1:3], 16)
            g = int(line_color[3:5], 16)
            b = int(line_color[5:7], 16)
            return f"rgba({r}, {g}, {b}, {self.fill_opacity})"
        return line_color

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def _build_traces(self) -> list[go.Scatter]:
        """Build the Plotly Scatter traces.

        Returns:
            List of configured :class:`go.Scatter` traces.
        """
        series_y = self._normalized_y()
        series_names = self._normalized_series_names()
        colors = self._resolve_line_colors()

        line_shape: str = "spline" if self.smooth else "linear"
        dash_style: str = self.line_style

        traces: list[go.Scatter] = []

        for s_idx, (series, name, color) in enumerate(
            zip(series_y, series_names, colors)
        ):
            marker_config: dict[str, object] | None = None
            if self.show_markers:
                marker_config = {
                    "size": self.marker_size,
                    "color": self.marker_color if self.marker_color is not None else color,
                    "line": {"color": color, "width": 1},
                }

            fill_mode: str = "tozeroy" if self.fill_area else "none"
            fillcolor: str | None = self._resolve_fill_color(color) if self.fill_area else None

            trace_kwargs: dict[str, object] = {
                "x": list(self.x),
                "y": series,
                "mode": "lines+markers" if self.show_markers else "lines",
                "name": name,
                "line": {
                    "color": color,
                    "width": self.line_width,
                    "dash": dash_style,
                    "shape": line_shape,
                },
                "marker": marker_config,
                "fill": fill_mode,
                "fillcolor": fillcolor,
            }

            if self.hover_template is not None:
                trace_kwargs["hovertemplate"] = self.hover_template

            # Future-ready: secondary y-axis support
            if self.secondary_y and s_idx == 1:
                trace_kwargs["yaxis"] = "y2"

            traces.append(go.Scatter(**trace_kwargs))

        return traces

    def _build_layout(self, fig: go.Figure) -> None:
        """Apply line-chart-specific layout styling to the figure.

        Args:
            fig: The figure to style (mutated in place).
        """
        show_legend = self.show_legend and self._is_multi_series()

        layout_kwargs: dict[str, object] = {
            "width": self.width,
            "height": self.height,
            "paper_bgcolor": self.paper_color,
            "plot_bgcolor": self.background_color,
            "font": dict(
                family=self.font_family,
                size=self.font_size,
                color=self.title_color,
            ),
            "title": {
                "text": self.title,
                "font": {
                    "family": self.font_family,
                    "size": self.font_size + 4,
                    "color": self.title_color,
                },
                "x": 0.5,
                "xanchor": "center",
            } if self.title else None,
            "showlegend": show_legend,
            "legend": dict(
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
            "margin": dict(l=70, r=70, t=80, b=80),
        }

        # Future-ready: secondary y-axis layout
        if self.secondary_y and self._is_multi_series():
            layout_kwargs["yaxis2"] = dict(
                title="",
                overlaying="y",
                side="right",
                showgrid=False,
                tickfont=dict(
                    family=self.font_family,
                    size=self.font_size - 1,
                    color=TEXT_SECONDARY,
                ),
            )

        fig.update_layout(**layout_kwargs)

    def _build_axes(self, fig: go.Figure) -> None:
        """Configure x- and y-axes with JESA theme styling.

        Args:
            fig: The figure to style (mutated in place).
        """
        grid_color = GRID if self.show_grid else "rgba(0,0,0,0)"

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

        # ``update_yaxes`` styles every y-axis. Reapply the secondary-axis
        # settings afterwards so it remains visually distinct from the score
        # axis used by the first series.
        if self.secondary_y and self._is_multi_series():
            fig.update_layout(
                yaxis2=dict(
                    title="",
                    overlaying="y",
                    side="right",
                    showgrid=False,
                    tickfont=dict(
                        family=self.font_family,
                        size=self.font_size - 1,
                        color=TEXT_SECONDARY,
                    ),
                )
            )

    def _build_hover(self, fig: go.Figure) -> None:
        """Configure hover label styling with the JESA palette.

        Args:
            fig: The figure to style (mutated in place).
        """
        fig.update_layout(
            hoverlabel=dict(
                font=dict(family=self.font_family, size=self.font_size),
                bgcolor=BACKGROUND,
                bordercolor=PRIMARY,
            )
        )

    def _build_annotations(self, fig: go.Figure) -> None:
        """Add user-provided annotations to the figure.

        Args:
            fig: The figure to style (mutated in place).
        """
        if self.annotations is not None:
            for ann in self.annotations:
                fig.add_annotation(**ann)
