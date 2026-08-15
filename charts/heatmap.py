"""Heatmap chart component for the JESA DMAT visualization package.

Provides a professional, industrial-grade heatmap built on Plotly's
:class:`go.Heatmap` trace with support for labelled rows and columns,
configurable colour scales, value annotations, missing-value handling,
data normalisation, and Industry-5.0 inspired default styling.

All colours are sourced from :mod:`charts.palette` to maintain visual
consistency across the application.

Usage::

    from charts.heatmap_chart import HeatmapChart

    heatmap = HeatmapChart(
        matrix=[
            [85, 72, 65],
            [90, 88, 70],
            [60, 75, 95],
        ],
        row_labels=["Strategy", "Technology", "People"],
        col_labels=["Q1", "Q2", "Q3"],
        title="Maturity Heatmap",
        show_values=True,
    )
    fig = heatmap.create()
    fig.show()

With custom colour scale::

    heatmap = HeatmapChart(
        matrix=[[1, 2], [3, 4]],
        row_labels=["A", "B"],
        col_labels=["X", "Y"],
        colorscale=[(0, "#EF4444"), (0.5, "#F59E0B"), (1, "#10B981")],
        zmin=0,
        zmax=5,
    )
    fig = heatmap.create()
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import plotly.graph_objects as go

from charts.palette import (
    BACKGROUND,
    BORDER,
    DEFAULT_FONT,
    GRID,
    PRIMARY,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from charts.utils import (
    validate_labels,
    validate_numeric_sequence,
)

__all__ = ["HeatmapChart"]

# ---------------------------------------------------------------------------
# Default layout constants
# ---------------------------------------------------------------------------
_DEFAULT_SHOW_VALUES: bool = True
_DEFAULT_TEXT_FORMAT: str = ".1f"
_DEFAULT_SHOW_COLORBAR: bool = True
_DEFAULT_SHOW_CELL_BORDERS: bool = True
_DEFAULT_MISSING_VALUE_COLOR: str = "#E2E8F0"
_DEFAULT_NORMALIZE: bool = False
_DEFAULT_BACKGROUND_COLOR: str = SURFACE
_DEFAULT_PAPER_COLOR: str = BACKGROUND
_DEFAULT_TITLE_COLOR: str = TEXT_PRIMARY
_DEFAULT_FONT_FAMILY: str = DEFAULT_FONT
_DEFAULT_FONT_SIZE: int = 14
_DEFAULT_WIDTH: int = 800
_DEFAULT_HEIGHT: int = 600


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


# =============================================================================
# HeatmapChart
# =============================================================================


@dataclass
class HeatmapChart:
    """Industrial-grade heatmap for matrix data visualisation.

    Encapsulates all configuration needed to render a Plotly heatmap
    with labelled rows and columns, optional value annotations,
    configurable colour scales, and missing-value handling.

    Call :meth:`create` to obtain the final ``go.Figure``.

    Args:
        matrix: Two-dimensional grid of numeric values. Each inner
            sequence represents one row. ``None`` values are treated as
            missing data and rendered with ``missing_value_color``.
        row_labels: Human-readable labels for each row. Must have the
            same length as the number of rows in ``matrix``.
        col_labels: Human-readable labels for each column. Must have the
            same length as the number of columns in ``matrix``.
        title: Chart title displayed above the figure (default ``""``).
        colorscale: Colour scale definition.

            * ``str`` – a named Plotly colour scale (e.g. ``"Viridis"``,
              ``"RdYlGn"``, ``"Blues"``).
            * ``Sequence[tuple[float, str]]`` – a custom scale where each
              tuple is ``(threshold, colour)`` with threshold in ``[0, 1]``.
            * ``None`` – Plotly's default colour scale is used.
        show_values: If ``True``, display the numeric value inside each
            cell (default ``True``).
        text_format: Python format string for cell annotations
            (default ``".1f"``). Examples: ``".0f"``, ``".2f"``, ``".1%"``.
        hover_template: Custom Plotly hover template. If ``None``, a
            sensible default is used.
        show_colorbar: If ``True``, display the colour bar legend
            (default ``True``).
        colorbar_title: Title displayed next to the colour bar
            (default ``""``).
        show_cell_borders: If ``True``, draw grid lines between cells
            (default ``True``).
        zmin: Explicit lower bound of the colour scale. If ``None``,
            computed from the data (default ``None``).
        zmax: Explicit upper bound of the colour scale. If ``None``,
            computed from the data (default ``None``).
        missing_value_color: Colour used for cells containing ``None``
            or ``NaN`` (default ``"#E2E8F0"``).
        normalize: If ``True``, linearly normalise the data to
            ``[0, 1]`` before mapping to colours. Original values are
            still displayed in annotations (default ``False``).
        background_color: Plot background colour (default :data:`SURFACE`).
        paper_color: Paper background colour (default :data:`BACKGROUND`).
        title_color: Colour of the title text (default :data:`TEXT_PRIMARY`).
        font_family: Font family for all text (default :data:`DEFAULT_FONT`).
        font_size: Base font size in pixels (default ``14``). Must be > 0.
        width: Figure width in pixels (default ``800``). Must be > 0.
        height: Figure height in pixels (default ``600``). Must be > 0.

    Raises:
        TypeError: If any argument has an invalid type.
        ValueError: If arguments violate business rules (empty matrix,
            inconsistent row lengths, duplicate labels, length mismatch,
            invalid colour scale, etc.).

    Example:
        Basic heatmap with annotations::

            >>> heatmap = HeatmapChart(
            ...     matrix=[
            ...         [85, 72, 65],
            ...         [90, 88, 70],
            ...         [60, 75, 95],
            ...     ],
            ...     row_labels=["Strategy", "Technology", "People"],
            ...     col_labels=["Q1", "Q2", "Q3"],
            ...     title="Maturity Heatmap",
            ... )
            >>> fig = heatmap.create()

        With missing values and custom scale::

            >>> heatmap = HeatmapChart(
            ...     matrix=[[1, None], [3, 4]],
            ...     row_labels=["A", "B"],
            ...     col_labels=["X", "Y"],
            ...     colorscale="RdYlGn",
            ...     missing_value_color="#94A3B8",
            ... )
            >>> fig = heatmap.create()
    """

    # -- required data -------------------------------------------------
    matrix: Sequence[Sequence[float | int | None]]
    row_labels: Sequence[str]
    col_labels: Sequence[str]

    # -- textual metadata ----------------------------------------------
    title: str = ""
    yaxis_title: str = ""

    # -- colour scale --------------------------------------------------
    colorscale: str | Sequence[tuple[float, str]] | None = None

    # -- annotations ---------------------------------------------------
    show_values: bool = _DEFAULT_SHOW_VALUES
    text_format: str = _DEFAULT_TEXT_FORMAT
    hover_template: str | None = None

    # -- colour bar ----------------------------------------------------
    show_colorbar: bool = _DEFAULT_SHOW_COLORBAR
    colorbar_title: str = ""

    # -- cell styling --------------------------------------------------
    show_cell_borders: bool = _DEFAULT_SHOW_CELL_BORDERS
    missing_value_color: str = _DEFAULT_MISSING_VALUE_COLOR

    # -- data transformation -------------------------------------------
    zmin: float | int | None = None
    zmax: float | int | None = None
    normalize: bool = _DEFAULT_NORMALIZE

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
        """Build and return the configured heatmap figure.

        Returns:
            A Plotly :class:`go.Figure` ready for rendering or export.

        Raises:
            TypeError: If any argument has an invalid type.
            ValueError: If data is inconsistent or violates business rules.
        """
        self._validate()
        primary_trace = self._build_heatmap()
        fig = go.Figure(data=[primary_trace])
        missing_trace = self._build_missing_value_overlay()
        if missing_trace is not None:
            fig.add_trace(missing_trace)
        self._build_annotations(fig)
        self._build_layout(fig)
        # Force no title (Plotly sometimes adds default when None)
        fig.update_layout(title=None)
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
        # -- matrix structure --------------------------------------------
        if not isinstance(self.matrix, Sequence) or isinstance(self.matrix, (str, bytes)):
            raise TypeError(
                f"matrix must be a sequence of sequences, got {type(self.matrix).__name__}"
            )
        if len(self.matrix) == 0:
            raise ValueError("matrix must not be empty")

        row_lengths: list[int] = []
        for r_idx, row in enumerate(self.matrix):
            if not isinstance(row, Sequence) or isinstance(row, (str, bytes)):
                raise TypeError(
                    f"matrix[{r_idx}] must be a sequence, got {type(row).__name__}"
                )
            if len(row) == 0:
                raise ValueError(f"matrix[{r_idx}] must not be empty")
            row_lengths.append(len(row))

            for c_idx, val in enumerate(row):
                if val is None:
                    continue
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    raise TypeError(
                        f"matrix[{r_idx}][{c_idx}] must be a number or None, "
                        f"got {type(val).__name__} (value={val!r})"
                    )

        # -- consistent row lengths --------------------------------------
        first_len = row_lengths[0]
        for r_idx, length in enumerate(row_lengths[1:], start=1):
            if length != first_len:
                raise ValueError(
                    f"All rows in matrix must have the same length. "
                    f"Row 0 has {first_len} columns, but row {r_idx} "
                    f"has {length} columns."
                )

        # -- row labels --------------------------------------------------
        validate_labels(self.row_labels, "row_labels")
        if len(self.row_labels) != len(self.matrix):
            raise ValueError(
                f"row_labels must have {len(self.matrix)} entries for "
                f"{len(self.matrix)} matrix rows, got {len(self.row_labels)}"
            )

        # -- duplicate row labels ----------------------------------------
        seen_rows: set[str] = set()
        for i, label in enumerate(self.row_labels):
            if label in seen_rows:
                raise ValueError(
                    f"Duplicate row label detected at index {i}: "
                    f"{label!r}. row_labels must be unique."
                )
            seen_rows.add(label)

        # -- column labels -----------------------------------------------
        validate_labels(self.col_labels, "col_labels")
        if len(self.col_labels) != first_len:
            raise ValueError(
                f"col_labels must have {first_len} entries for "
                f"{first_len} matrix columns, got {len(self.col_labels)}"
            )

        # -- duplicate column labels -------------------------------------
        seen_cols: set[str] = set()
        for i, label in enumerate(self.col_labels):
            if label in seen_cols:
                raise ValueError(
                    f"Duplicate column label detected at index {i}: "
                    f"{label!r}. col_labels must be unique."
                )
            seen_cols.add(label)

        # -- colorscale validation ---------------------------------------
        if self.colorscale is not None and not isinstance(self.colorscale, str):
            if not isinstance(self.colorscale, Sequence) or isinstance(self.colorscale, (str, bytes)):
                raise TypeError(
                    f"colorscale must be str, Sequence[tuple[float, str]], or None, "
                    f"got {type(self.colorscale).__name__}"
                )
            for i, entry in enumerate(self.colorscale):
                if not isinstance(entry, tuple) or len(entry) != 2:
                    raise TypeError(
                        f"colorscale[{i}] must be a tuple of (threshold, color), "
                        f"got {entry!r}"
                    )
                threshold, color = entry
                if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
                    raise TypeError(
                        f"colorscale[{i}] threshold must be a number, "
                        f"got {type(threshold).__name__}"
                    )
                if not 0.0 <= float(threshold) <= 1.0:
                    raise ValueError(
                        f"colorscale[{i}] threshold must be between 0.0 and 1.0, "
                        f"got {threshold}"
                    )
                if not isinstance(color, str):
                    raise TypeError(
                        f"colorscale[{i}] color must be str, got {type(color).__name__}"
                    )

        # -- zmin / zmax types -------------------------------------------
        for name, val in [("zmin", self.zmin), ("zmax", self.zmax)]:
            if val is not None:
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    raise TypeError(
                        f"{name} must be a number or None, got {type(val).__name__}"
                    )

        # -- zmin < zmax -------------------------------------------------
        if self.zmin is not None and self.zmax is not None:
            if self.zmin >= self.zmax:
                raise ValueError(
                    f"zmin ({self.zmin}) must be < zmax ({self.zmax})"
                )

        # -- dimensions & font -------------------------------------------
        _validate_positive_int("width", self.width)
        _validate_positive_int("height", self.height)
        _validate_positive_int("font_size", self.font_size)

        # -- string types ------------------------------------------------
        _validate_str_or_none("title", self.title)
        _validate_str("text_format", self.text_format)
        _validate_str_or_none("hover_template", self.hover_template)
        _validate_str("colorbar_title", self.colorbar_title)
        _validate_str("missing_value_color", self.missing_value_color)
        _validate_str("font_family", self.font_family)

        # -- boolean types -----------------------------------------------
        for name in ("show_values", "show_colorbar", "show_cell_borders", "normalize"):
            val = getattr(self, name)
            if not isinstance(val, bool):
                raise TypeError(
                    f"{name} must be bool, got {type(val).__name__}"
                )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_numeric_matrix(self) -> list[list[float]]:
        """Convert the raw matrix to a pure numeric matrix.

        ``None`` values are replaced with ``float('nan')`` so that
        Plotly treats them as missing data.

        Returns:
            Two-dimensional list of floats.
        """
        return [
            [float(val) if val is not None else float("nan") for val in row]
            for row in self.matrix
        ]

    def _compute_zmin_zmax(self, data: list[list[float]]) -> tuple[float, float]:
        """Compute the effective zmin and zmax for the colour scale.

        If explicit ``zmin`` or ``zmax`` were provided, returns them.
        Otherwise computes from the data, ignoring NaN values.

        Args:
            data: Numeric matrix (NaN for missing values).

        Returns:
            Tuple of ``(zmin, zmax)``.
        """
        flat = [v for row in data for v in row if not math.isnan(v)]
        if len(flat) == 0:
            return (0.0, 1.0)

        data_min = min(flat)
        data_max = max(flat)

        if data_min == data_max:
            return (data_min - 0.5, data_max + 0.5)

        resolved_min = float(self.zmin) if self.zmin is not None else data_min
        resolved_max = float(self.zmax) if self.zmax is not None else data_max
        return (resolved_min, resolved_max)

    def _normalise_matrix(self, data: list[list[float]], zmin: float, zmax: float) -> list[list[float]]:
        """Linearly normalise a numeric matrix to ``[0, 1]``.

        Missing values (NaN) are preserved.

        Args:
            data: Numeric matrix.
            zmin: Lower bound.
            zmax: Upper bound.

        Returns:
            Normalised matrix.
        """
        span = zmax - zmin
        if span == 0:
            return [[0.0 if not math.isnan(v) else float("nan") for v in row] for row in data]
        return [
            [(v - zmin) / span if not math.isnan(v) else float("nan") for v in row]
            for row in data
        ]

    def _resolve_colorscale(self) -> str | list[list[object]] | None:
        """Resolve the colour scale definition for Plotly.

        Returns:
            Either a named scale string, a Plotly-compatible list of
            ``[threshold, colour]`` lists, or ``None`` for the default.
        """
        if self.colorscale is None:
            return None
        if isinstance(self.colorscale, str):
            return self.colorscale
        # Convert Sequence[tuple[float, str]] → list[list[object]]
        return [[threshold, color] for threshold, color in self.colorscale]

    def _format_cell_text(self, val: float | None) -> str:
        """Format a single cell value for annotation display.

        Args:
            val: The cell value, or ``None`` for missing data.

        Returns:
            Formatted string or empty string for missing values.
        """
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return ""
        try:
            return f"{val:{self.text_format}}"
        except ValueError:
            return str(val)

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def _build_heatmap(self) -> go.Heatmap:
        """Build the Plotly Heatmap trace.

        Returns:
            Configured :class:`go.Heatmap`.
        """
        data = self._to_numeric_matrix()
        zmin, zmax = self._compute_zmin_zmax(data)

        plot_data = data
        if self.normalize:
            plot_data = self._normalise_matrix(data, zmin, zmax)
            zmin, zmax = 0.0, 1.0

        colorscale = self._resolve_colorscale()

        hovertemplate = self.hover_template
        if hovertemplate is None:
            hovertemplate = (
                "<b>%{y}</b> / <b>%{x}</b><br>"
                "Value: %{z}<extra></extra>"
            )

        trace_kwargs: dict[str, object] = {
            "z": plot_data,
            "x": list(self.col_labels),
            "y": list(self.row_labels),
            "colorscale": colorscale,
            "showscale": self.show_colorbar,
            "zmin": zmin,
            "zmax": zmax,
            "hovertemplate": hovertemplate,
        }

        if self.show_colorbar:
            trace_kwargs["colorbar"] = {
                "title": {
                    "text": self.colorbar_title,
                    "font": {
                        "family": self.font_family,
                        "size": self.font_size,
                        "color": self.title_color,
                    },
                },
                "tickfont": {
                    "family": self.font_family,
                    "size": self.font_size - 1,
                    "color": TEXT_SECONDARY,
                },
                "outlinecolor": BORDER,
                "outlinewidth": 1,
            }

        return go.Heatmap(**trace_kwargs)

    def _build_missing_value_overlay(self) -> go.Heatmap | None:
        """Build an overlay trace for missing values using the missing colour."""
        if self.missing_value_color is None:
            return None

        data = self._to_numeric_matrix()
        missing_mask = [
            [1.0 if math.isnan(val) else float('nan') for val in row]
            for row in data
        ]
        if all(math.isnan(val) for row in missing_mask for val in row):
            return None

        return go.Heatmap(
            z=missing_mask,
            x=list(self.col_labels),
            y=list(self.row_labels),
            colorscale=[[0, self.missing_value_color], [1, self.missing_value_color]],
            showscale=False,
            hoverinfo="skip",
            zmin=0,
            zmax=1,
        )

    def _build_annotations(self, fig: go.Figure) -> None:
        """Add value annotations inside each heatmap cell.

        Args:
            fig: The figure to annotate (mutated in place).
        """
        if not self.show_values:
            return

        annotations: list[dict[str, object]] = []
        for r_idx, row in enumerate(self.matrix):
            for c_idx, val in enumerate(row):
                text = self._format_cell_text(val)
                font_color = (
                    TEXT_PRIMARY
                    if val is not None and not (isinstance(val, float) and math.isnan(val))
                    else TEXT_SECONDARY
                )
                annotations.append({
                    "x": self.col_labels[c_idx],
                    "y": self.row_labels[r_idx],
                    "text": text,
                    "showarrow": False,
                    "font": {
                        "family": self.font_family,
                        "size": self.font_size - 1,
                        "color": font_color,
                    },
                })

        fig.update_layout(annotations=annotations)

    def _build_layout(self, fig: go.Figure) -> None:
        """Apply heatmap-specific layout styling to the figure.

        Args:
            fig: The figure to style (mutated in place).
        """
        grid_color = GRID if self.show_cell_borders else "rgba(0,0,0,0)"

        # Determine if we should show a title
        title_value = None
        if self.title is not None:
            title_str = str(self.title).strip()
            if title_str and title_str.lower() != "undefined":
                title_value = {
                    "text": title_str,
                    "font": {
                        "family": self.font_family,
                        "size": self.font_size + 4,
                        "color": self.title_color,
                    },
                    "x": 0.5,
                    "xanchor": "center",
                }

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
            title=title_value,
            margin=dict(l=80, r=80, t=80, b=80),
        )

        fig.update_xaxes(
            side="top",
            showgrid=self.show_cell_borders,
            gridcolor=grid_color,
            zeroline=False,
            linecolor=BORDER,
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
            showgrid=self.show_cell_borders,
            gridcolor=grid_color,
            zeroline=False,
            linecolor=BORDER,
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
            autorange="reversed",
        )