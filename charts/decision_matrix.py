"""Decision matrix component for the JESA DMAT visualization package.

Provides a professional, industrial-grade prioritisation matrix
(Impact vs Effort) built on Plotly's :class:`go.Scatter` trace.
Designed for the JESA DMAT decision engine to visualise and prioritise
recommendations across four strategic quadrants.

Each recommendation is plotted as a point whose horizontal position
represents Effort and vertical position represents Impact. The matrix
is divided into four quadrants by configurable thresholds:

* **Quick Wins** (low effort, high impact) — top-left
* **Strategic Projects** (high effort, high impact) — top-right
* **Low Priority** (low effort, low impact) — bottom-left
* **Avoid** (high effort, low impact) — bottom-right

All colours are sourced from :mod:`charts.palette` to maintain visual
consistency across the application.

Usage::

    from charts.decision_matrix import DecisionMatrix, Recommendation

    matrix = DecisionMatrix(
        recommendations=[
            Recommendation(name="Deploy MES", impact=92, effort=81, category="Technology"),
            Recommendation(name="Train Staff", impact=75, effort=30, category="People"),
            Recommendation(name="Upgrade ERP", impact=60, effort=85, category="Technology"),
            Recommendation(name="Audit Process", impact=40, effort=25, category="Process"),
        ],
        title="Prioritisation Matrix",
    )
    fig = matrix.create()
    fig.show()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import plotly.graph_objects as go

from charts.palette import (
    BACKGROUND,
    BORDER,
    DEFAULT_FONT,
    ERROR,
    GRID,
    INFO,
    PRIMARY,
    QUALITATIVE_COLORS,
    SUCCESS,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING,
)
from charts.utils import (
    generate_colors,
    unique_labels,
)

__all__ = [
    "Recommendation",
    "QuadrantLabels",
    "QuadrantColors",
    "DecisionMatrix",
]

# ---------------------------------------------------------------------------
# Default constants
# ---------------------------------------------------------------------------
_DEFAULT_X_THRESHOLD: float = 50.0
_DEFAULT_Y_THRESHOLD: float = 50.0
_DEFAULT_POINT_SIZE: int = 14
_DEFAULT_SHOW_QUADRANT_LABELS: bool = True
_DEFAULT_SHOW_QUADRANT_BACKGROUNDS: bool = True
_DEFAULT_SHOW_THRESHOLD_LINES: bool = True
_DEFAULT_SHOW_LEGEND: bool = True
_DEFAULT_TEXT_POSITION: str = "top center"
_DEFAULT_BACKGROUND_COLOR: str = SURFACE
_DEFAULT_PAPER_COLOR: str = BACKGROUND
_DEFAULT_TITLE_COLOR: str = TEXT_PRIMARY
_DEFAULT_FONT_FAMILY: str = DEFAULT_FONT
_DEFAULT_FONT_SIZE: int = 14
_DEFAULT_WIDTH: int = 900
_DEFAULT_HEIGHT: int = 700
_DEFAULT_MIN_IMPACT: float = 0.0
_DEFAULT_MAX_IMPACT: float = 100.0
_DEFAULT_MIN_EFFORT: float = 0.0
_DEFAULT_MAX_EFFORT: float = 100.0


# ---------------------------------------------------------------------------
# Private validation helpers
# ---------------------------------------------------------------------------


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


def _validate_percentage(name: str, value: object) -> None:
    """Raise TypeError/ValueError if ``value`` is not a number in [0, 100].

    Args:
        name: Parameter name for error messages.
        value: Value to validate.

    Raises:
        TypeError: If ``value`` is not a number (bools rejected).
        ValueError: If ``value`` is outside ``[0, 100]``.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(
            f"{name} must be a number, got {type(value).__name__}"
        )
    if not 0.0 <= float(value) <= 100.0:
        raise ValueError(
            f"{name} must be between 0.0 and 100.0, got {value}"
        )


# =============================================================================
# Recommendation
# =============================================================================


@dataclass
class Recommendation:
    """A single recommendation to be plotted on the decision matrix.

    Args:
        name: Human-readable name displayed as a label next to the point.
            Must be a non-empty string.
        impact: Impact score on a 0–100 scale. Higher is better.
        effort: Effort score on a 0–100 scale. Higher means more costly.
        category: Logical grouping used for colour coding and legend.
            Must be a non-empty string.

    Raises:
        TypeError: If any field has an incorrect type.
        ValueError: If ``impact`` or ``effort`` is outside ``[0, 100]``,
            or if ``name`` / ``category`` is empty.

    Example:
        >>> rec = Recommendation(
        ...     name="Deploy MES",
        ...     impact=92,
        ...     effort=81,
        ...     category="Technology",
        ... )
    """

    name: str
    impact: float | int
    effort: float | int
    category: str

    def __post_init__(self) -> None:
        """Validate fields after dataclass initialisation."""
        _validate_str("name", self.name)
        if self.name.strip() == "":
            raise ValueError("name must not be an empty or whitespace-only string")

        _validate_str("category", self.category)
        if self.category.strip() == "":
            raise ValueError(
                "category must not be an empty or whitespace-only string"
            )

        _validate_percentage("impact", self.impact)
        _validate_percentage("effort", self.effort)


# =============================================================================
# QuadrantLabels
# =============================================================================


@dataclass
class QuadrantLabels:
    """Human-readable labels for the four decision-matrix quadrants.

    Args:
        quick_wins: Top-left quadrant label (low effort, high impact).
        strategic: Top-right quadrant label (high effort, high impact).
        low_priority: Bottom-left quadrant label (low effort, low impact).
        avoid: Bottom-right quadrant label (high effort, low impact).

    Example:
        >>> labels = QuadrantLabels(
        ...     quick_wins="Quick Wins",
        ...     strategic="Major Projects",
        ...     low_priority="Fill-ins",
        ...     avoid="Thankless",
        ... )
    """

    quick_wins: str = "Quick Wins"
    strategic: str = "Strategic Projects"
    low_priority: str = "Low Priority"
    avoid: str = "Avoid"

    def __post_init__(self) -> None:
        """Validate that all labels are non-empty strings."""
        for field_name in ("quick_wins", "strategic", "low_priority", "avoid"):
            value = getattr(self, field_name)
            _validate_str(field_name, value)
            if value.strip() == "":
                raise ValueError(
                    f"QuadrantLabels.{field_name} must not be an empty "
                    f"or whitespace-only string"
                )


# =============================================================================
# QuadrantColors
# =============================================================================


@dataclass
class QuadrantColors:
    """Background colours for the four decision-matrix quadrants.

    Colours are expected to be Plotly-compatible strings (hex, rgb, rgba,
    or named CSS colours). Low opacity is recommended so that the grid
    and points remain clearly visible.

    Args:
        quick_wins: Top-left quadrant background colour.
        strategic: Top-right quadrant background colour.
        low_priority: Bottom-left quadrant background colour.
        avoid: Bottom-right quadrant background colour.

    Example:
        >>> colors = QuadrantColors(
        ...     quick_wins="rgba(16, 185, 129, 0.08)",
        ...     strategic="rgba(59, 130, 246, 0.08)",
        ...     low_priority="rgba(245, 158, 11, 0.08)",
        ...     avoid="rgba(239, 68, 68, 0.08)",
        ... )
    """

    quick_wins: str = "rgba(16, 185, 129, 0.08)"
    strategic: str = "rgba(59, 130, 246, 0.08)"
    low_priority: str = "rgba(245, 158, 11, 0.08)"
    avoid: str = "rgba(239, 68, 68, 0.08)"

    def __post_init__(self) -> None:
        """Validate that all colours are strings."""
        for field_name in ("quick_wins", "strategic", "low_priority", "avoid"):
            value = getattr(self, field_name)
            _validate_str(field_name, value)


# =============================================================================
# DecisionMatrix
# =============================================================================


@dataclass
class DecisionMatrix:
    """Industrial-grade decision matrix for recommendation prioritisation.

    Plots recommendations on a two-dimensional Impact vs Effort plane
    divided into four strategic quadrants. Supports category-based colour
    coding, configurable thresholds, quadrant labels, and rich hover
    interactivity.

    Call :meth:`create` to obtain the final ``go.Figure``.

    Args:
        recommendations: Sequence of :class:`Recommendation` instances to
            plot. Must be non-empty. Duplicate names are rejected.
        title: Chart title displayed above the figure (default ``""``).
        x_threshold: Horizontal separation between low-effort (left) and
            high-effort (right) quadrants (default ``50.0``).
            Must be in ``[0, 100]``.
        y_threshold: Vertical separation between low-impact (bottom) and
            high-impact (top) quadrants (default ``50.0``).
            Must be in ``[0, 100]``.
        quadrant_labels: Custom labels for the four quadrants
            (default :class:`QuadrantLabels` with standard names).
        quadrant_colors: Custom background colours for the four quadrants
            (default :class:`QuadrantColors` with low-opacity tints).
        category_colors: Optional mapping from category name to colour.
            If ``None``, colours are automatically generated from
            :data:`QUALITATIVE_COLORS`.
        point_size: Diameter of the scatter markers in pixels
            (default ``14``). Must be > 0.
        text_position: Position of the recommendation name relative to
            its marker — ``"top center"`` (default), ``"middle right"``,
            ``"bottom center"``, etc.
        show_quadrant_labels: If ``True``, display quadrant names as
            background annotations (default ``True``).
        show_quadrant_backgrounds: If ``True``, tint each quadrant with
            its background colour (default ``True``).
        show_threshold_lines: If ``True``, draw dashed threshold lines
            (default ``True``).
        show_legend: If ``True``, display the category legend
            (default ``True``).
        hover_template: Custom Plotly hover template. If ``None``, a
            rich default is used showing name, impact, effort, and
            category.
        background_color: Plot background colour (default :data:`SURFACE`).
        paper_color: Paper background colour (default :data:`BACKGROUND`).
        title_color: Colour of the title text (default :data:`TEXT_PRIMARY`).
        font_family: Font family for all text (default :data:`DEFAULT_FONT`).
        font_size: Base font size in pixels (default ``14``). Must be > 0.
        width: Figure width in pixels (default ``900``). Must be > 0.
        height: Figure height in pixels (default ``700``). Must be > 0.

    Raises:
        TypeError: If any argument has an invalid type.
        ValueError: If arguments violate business rules (empty data,
            duplicate names, threshold out of range, etc.).

    Example:
        >>> matrix = DecisionMatrix(
        ...     recommendations=[
        ...         Recommendation("Deploy MES", 92, 81, "Technology"),
        ...         Recommendation("Train Staff", 75, 30, "People"),
        ...         Recommendation("Upgrade ERP", 60, 85, "Technology"),
        ...         Recommendation("Audit Process", 40, 25, "Process"),
        ...     ],
        ...     title="Prioritisation Matrix",
        ...     x_threshold=50,
        ...     y_threshold=50,
        ... )
        >>> fig = matrix.create()
    """

    # -- required data -------------------------------------------------
    recommendations: Sequence[Recommendation]

    # -- textual metadata ----------------------------------------------
    title: str = ""

    # -- quadrant configuration ----------------------------------------
    x_threshold: float | int = _DEFAULT_X_THRESHOLD
    y_threshold: float | int = _DEFAULT_Y_THRESHOLD
    quadrant_labels: QuadrantLabels = field(default_factory=QuadrantLabels)
    quadrant_colors: QuadrantColors = field(default_factory=QuadrantColors)

    # -- visual styling ------------------------------------------------
    category_colors: dict[str, str] | None = None
    point_size: int = _DEFAULT_POINT_SIZE
    text_position: str = _DEFAULT_TEXT_POSITION
    show_quadrant_labels: bool = _DEFAULT_SHOW_QUADRANT_LABELS
    show_quadrant_backgrounds: bool = _DEFAULT_SHOW_QUADRANT_BACKGROUNDS
    show_threshold_lines: bool = _DEFAULT_SHOW_THRESHOLD_LINES
    show_legend: bool = _DEFAULT_SHOW_LEGEND
    hover_template: str | None = None

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
        """Build and return the configured decision matrix figure.

        Returns:
            A Plotly :class:`go.Figure` ready for rendering or export.

        Raises:
            TypeError: If any argument has an invalid type.
            ValueError: If data is inconsistent or violates business rules.
        """
        self._validate()
        fig = go.Figure()
        self._build_quadrant_backgrounds(fig)
        self._build_threshold_lines(fig)
        self._build_scatter_traces(fig)
        self._build_quadrant_annotations(fig)
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
        # -- recommendations ---------------------------------------------
        if not isinstance(self.recommendations, Sequence):
            raise TypeError(
                f"recommendations must be a sequence, got {type(self.recommendations).__name__}"
            )
        if len(self.recommendations) == 0:
            raise ValueError("recommendations must not be empty")

        seen_names: set[str] = set()
        for i, rec in enumerate(self.recommendations):
            if not isinstance(rec, Recommendation):
                raise TypeError(
                    f"recommendations[{i}] must be Recommendation, "
                    f"got {type(rec).__name__}"
                )
            if rec.name in seen_names:
                raise ValueError(
                    f"Duplicate recommendation name detected at index {i}: "
                    f"{rec.name!r}. All recommendation names must be unique."
                )
            seen_names.add(rec.name)

        # -- thresholds --------------------------------------------------
        _validate_percentage("x_threshold", self.x_threshold)
        _validate_percentage("y_threshold", self.y_threshold)

        # -- dimensions & font -------------------------------------------
        _validate_positive_int("width", self.width)
        _validate_positive_int("height", self.height)
        _validate_positive_int("font_size", self.font_size)
        _validate_positive_int("point_size", self.point_size)

        # -- string types ------------------------------------------------
        _validate_str("title", self.title)
        _validate_str("text_position", self.text_position)
        _validate_str_or_none("hover_template", self.hover_template)
        _validate_str("font_family", self.font_family)
        _validate_str("background_color", self.background_color)
        _validate_str("paper_color", self.paper_color)
        _validate_str("title_color", self.title_color)

        # -- boolean types -----------------------------------------------
        for name in (
            "show_quadrant_labels",
            "show_quadrant_backgrounds",
            "show_threshold_lines",
            "show_legend",
        ):
            val = getattr(self, name)
            if not isinstance(val, bool):
                raise TypeError(
                    f"{name} must be bool, got {type(val).__name__}"
                )

        # -- category_colors validation ----------------------------------
        if self.category_colors is not None:
            if not isinstance(self.category_colors, dict):
                raise TypeError(
                    f"category_colors must be dict or None, got {type(self.category_colors).__name__}"
                )
            categories = self._extract_categories()
            for cat in categories:
                if cat not in self.category_colors:
                    raise ValueError(
                        f"category_colors is missing an entry for category {cat!r}"
                    )
            for cat, color in self.category_colors.items():
                if not isinstance(color, str):
                    raise TypeError(
                        f"category_colors[{cat!r}] must be str, got {type(color).__name__}"
                    )

        # -- quadrant_labels & quadrant_colors types ---------------------
        if not isinstance(self.quadrant_labels, QuadrantLabels):
            raise TypeError(
                f"quadrant_labels must be QuadrantLabels, got {type(self.quadrant_labels).__name__}"
            )
        if not isinstance(self.quadrant_colors, QuadrantColors):
            raise TypeError(
                f"quadrant_colors must be QuadrantColors, got {type(self.quadrant_colors).__name__}"
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_categories(self) -> list[str]:
        """Return the sorted list of unique category names.

        Returns:
            Sorted list of unique category strings.
        """
        return sorted({rec.category for rec in self.recommendations})

    def _resolve_category_colors(self) -> dict[str, str]:
        """Resolve the colour mapping for all categories.

        Uses custom colours if provided, otherwise generates from
        :data:`QUALITATIVE_COLORS`.

        Returns:
            Dictionary mapping category name to hex colour string.
        """
        if self.category_colors is not None:
            return dict(self.category_colors)
        categories = self._extract_categories()
        colors = generate_colors(QUALITATIVE_COLORS, len(categories))
        return dict(zip(categories, colors))

    def _group_by_category(self) -> dict[str, list[Recommendation]]:
        """Group recommendations by their category.

        Returns:
            Dictionary mapping category name to list of recommendations.
        """
        groups: dict[str, list[Recommendation]] = {}
        for rec in self.recommendations:
            groups.setdefault(rec.category, []).append(rec)
        return groups

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def _build_quadrant_backgrounds(self, fig: go.Figure) -> None:
        """Add semi-transparent background rectangles for each quadrant.

        Args:
            fig: The figure to decorate (mutated in place).
        """
        if not self.show_quadrant_backgrounds:
            return

        x_t = float(self.x_threshold)
        y_t = float(self.y_threshold)

        quadrants = [
            (0, y_t, x_t, 100, self.quadrant_colors.quick_wins),      # top-left
            (x_t, y_t, 100, 100, self.quadrant_colors.strategic),      # top-right
            (0, 0, x_t, y_t, self.quadrant_colors.low_priority),       # bottom-left
            (x_t, 0, 100, y_t, self.quadrant_colors.avoid),            # bottom-right
        ]

        for x0, y0, x1, y1, fillcolor in quadrants:
            fig.add_shape(
                type="rect",
                x0=x0,
                y0=y0,
                x1=x1,
                y1=y1,
                fillcolor=fillcolor,
                line_width=0,
                layer="below",
            )

    def _build_threshold_lines(self, fig: go.Figure) -> None:
        """Add dashed threshold lines to separate quadrants.

        Args:
            fig: The figure to decorate (mutated in place).
        """
        if not self.show_threshold_lines:
            return

        fig.add_hline(
            y=float(self.y_threshold),
            line_dash="dash",
            line_color=BORDER,
            line_width=2,
            layer="above",
        )
        fig.add_vline(
            x=float(self.x_threshold),
            line_dash="dash",
            line_color=BORDER,
            line_width=2,
            layer="above",
        )

    def _build_scatter_traces(self, fig: go.Figure) -> None:
        """Add one Scatter trace per category.

        Args:
            fig: The figure to populate (mutated in place).
        """
        groups = self._group_by_category()
        colors = self._resolve_category_colors()

        default_hover = (
            "<b>%{customdata[0]}</b><br>"
            "Impact: %{y:.1f}<br>"
            "Effort: %{x:.1f}<br>"
            "Category: %{customdata[1]}<extra></extra>"
        )
        hovertemplate = self.hover_template if self.hover_template is not None else default_hover

        for category in sorted(groups.keys()):
            recs = groups[category]
            color = colors[category]

            fig.add_trace(go.Scatter(
                x=[rec.effort for rec in recs],
                y=[rec.impact for rec in recs],
                mode="markers+text",
                name=category,
                text=[rec.name for rec in recs],
                textposition=self.text_position,
                marker=dict(
                    size=self.point_size,
                    color=color,
                    line=dict(color=TEXT_PRIMARY, width=1),
                    symbol="circle",
                ),
                textfont=dict(
                    family=self.font_family,
                    size=self.font_size - 1,
                    color=TEXT_PRIMARY,
                ),
                customdata=[[rec.name, rec.category] for rec in recs],
                hovertemplate=hovertemplate,
            ))

    def _build_quadrant_annotations(self, fig: go.Figure) -> None:
        """Add quadrant name annotations at the centre of each zone.

        Args:
            fig: The figure to annotate (mutated in place).
        """
        if not self.show_quadrant_labels:
            return

        x_t = float(self.x_threshold)
        y_t = float(self.y_threshold)

        annotations = [
            (x_t / 2, (100 + y_t) / 2, self.quadrant_labels.quick_wins),
            ((100 + x_t) / 2, (100 + y_t) / 2, self.quadrant_labels.strategic),
            (x_t / 2, y_t / 2, self.quadrant_labels.low_priority),
            ((100 + x_t) / 2, y_t / 2, self.quadrant_labels.avoid),
        ]

        for x, y, text in annotations:
            fig.add_annotation(
                x=x,
                y=y,
                text=f"<b>{text}</b>",
                showarrow=False,
                font=dict(
                    family=self.font_family,
                    size=self.font_size + 2,
                    color=TEXT_SECONDARY,
                ),
                opacity=0.35,
                xref="x",
                yref="y",
            )

    def _build_layout(self, fig: go.Figure) -> None:
        """Apply decision-matrix-specific layout styling.

        Args:
            fig: The figure to style (mutated in place).
        """
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
            showlegend=self.show_legend,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(
                    family=self.font_family,
                    size=self.font_size,
                    color=TEXT_SECONDARY,
                ),
            ),
            margin=dict(l=60, r=60, t=80, b=80),
            xaxis=dict(
                title="Effort →",
                range=[_DEFAULT_MIN_EFFORT, _DEFAULT_MAX_EFFORT],
                showgrid=True,
                gridcolor=GRID,
                zeroline=False,
                linecolor=BORDER,
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
            ),
            yaxis=dict(
                title="Impact →",
                range=[_DEFAULT_MIN_IMPACT, _DEFAULT_MAX_IMPACT],
                showgrid=True,
                gridcolor=GRID,
                zeroline=False,
                linecolor=BORDER,
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
                scaleanchor="x",
                scaleratio=1,
            ),
            hoverlabel=dict(
                font=dict(family=self.font_family, size=self.font_size),
                bgcolor=BACKGROUND,
                bordercolor=PRIMARY,
            ),
        )


def _validate_percentage(name: str, value: object) -> None:
    """Raise TypeError/ValueError if ``value`` is not a number in [0, 100].

    Args:
        name: Parameter name for error messages.
        value: Value to validate.

    Raises:
        TypeError: If ``value`` is not a number (bools rejected).
        ValueError: If ``value`` is outside ``[0, 100]``.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(
            f"{name} must be a number, got {type(value).__name__}"
        )
    if not 0.0 <= float(value) <= 100.0:
        raise ValueError(
            f"{name} must be between 0.0 and 100.0, got {value}"
        )


# =============================================================================
# Recommendation
# =============================================================================


@dataclass
class Recommendation:
    """A single recommendation to be plotted on the decision matrix.

    Args:
        name: Human-readable name displayed as a label next to the point.
            Must be a non-empty string.
        impact: Impact score on a 0–100 scale. Higher is better.
        effort: Effort score on a 0–100 scale. Higher means more costly.
        category: Logical grouping used for colour coding and legend.
            Must be a non-empty string.

    Raises:
        TypeError: If any field has an incorrect type.
        ValueError: If ``impact`` or ``effort`` is outside ``[0, 100]``,
            or if ``name`` / ``category`` is empty.

    Example:
        >>> rec = Recommendation(
        ...     name="Deploy MES",
        ...     impact=92,
        ...     effort=81,
        ...     category="Technology",
        ... )
    """

    name: str
    impact: float | int
    effort: float | int
    category: str

    def __post_init__(self) -> None:
        """Validate fields after dataclass initialisation."""
        _validate_str("name", self.name)
        if self.name.strip() == "":
            raise ValueError("name must not be an empty or whitespace-only string")

        _validate_str("category", self.category)
        if self.category.strip() == "":
            raise ValueError(
                "category must not be an empty or whitespace-only string"
            )

        _validate_percentage("impact", self.impact)
        _validate_percentage("effort", self.effort)


# =============================================================================
# QuadrantLabels
# =============================================================================


@dataclass
class QuadrantLabels:
    """Human-readable labels for the four decision-matrix quadrants.

    Args:
        quick_wins: Top-left quadrant label (low effort, high impact).
        strategic: Top-right quadrant label (high effort, high impact).
        low_priority: Bottom-left quadrant label (low effort, low impact).
        avoid: Bottom-right quadrant label (high effort, low impact).

    Example:
        >>> labels = QuadrantLabels(
        ...     quick_wins="Quick Wins",
        ...     strategic="Major Projects",
        ...     low_priority="Fill-ins",
        ...     avoid="Thankless",
        ... )
    """

    quick_wins: str = "Quick Wins"
    strategic: str = "Strategic Projects"
    low_priority: str = "Low Priority"
    avoid: str = "Avoid"

    def __post_init__(self) -> None:
        """Validate that all labels are non-empty strings."""
        for field_name in ("quick_wins", "strategic", "low_priority", "avoid"):
            value = getattr(self, field_name)
            _validate_str(field_name, value)
            if value.strip() == "":
                raise ValueError(
                    f"QuadrantLabels.{field_name} must not be an empty "
                    f"or whitespace-only string"
                )


# =============================================================================
# QuadrantColors
# =============================================================================


@dataclass
class QuadrantColors:
    """Background colours for the four decision-matrix quadrants.

    Colours are expected to be Plotly-compatible strings (hex, rgb, rgba,
    or named CSS colours). Low opacity is recommended so that the grid
    and points remain clearly visible.

    Args:
        quick_wins: Top-left quadrant background colour.
        strategic: Top-right quadrant background colour.
        low_priority: Bottom-left quadrant background colour.
        avoid: Bottom-right quadrant background colour.

    Example:
        >>> colors = QuadrantColors(
        ...     quick_wins="rgba(16, 185, 129, 0.08)",
        ...     strategic="rgba(59, 130, 246, 0.08)",
        ...     low_priority="rgba(245, 158, 11, 0.08)",
        ...     avoid="rgba(239, 68, 68, 0.08)",
        ... )
    """

    quick_wins: str = "rgba(16, 185, 129, 0.08)"
    strategic: str = "rgba(59, 130, 246, 0.08)"
    low_priority: str = "rgba(245, 158, 11, 0.08)"
    avoid: str = "rgba(239, 68, 68, 0.08)"

    def __post_init__(self) -> None:
        """Validate that all colours are strings."""
        for field_name in ("quick_wins", "strategic", "low_priority", "avoid"):
            value = getattr(self, field_name)
            _validate_str(field_name, value)


# =============================================================================
# DecisionMatrix
# =============================================================================


@dataclass
class DecisionMatrix:
    """Industrial-grade decision matrix for recommendation prioritisation.

    Plots recommendations on a two-dimensional Impact vs Effort plane
    divided into four strategic quadrants. Supports category-based colour
    coding, configurable thresholds, quadrant labels, and rich hover
    interactivity.

    Call :meth:`create` to obtain the final ``go.Figure``.

    Args:
        recommendations: Sequence of :class:`Recommendation` instances to
            plot. Must be non-empty. Duplicate names are rejected.
        title: Chart title displayed above the figure (default ``""``).
        x_threshold: Horizontal separation between low-effort (left) and
            high-effort (right) quadrants (default ``50.0``).
            Must be in ``[0, 100]``.
        y_threshold: Vertical separation between low-impact (bottom) and
            high-impact (top) quadrants (default ``50.0``).
            Must be in ``[0, 100]``.
        quadrant_labels: Custom labels for the four quadrants
            (default :class:`QuadrantLabels` with standard names).
        quadrant_colors: Custom background colours for the four quadrants
            (default :class:`QuadrantColors` with low-opacity tints).
        category_colors: Optional mapping from category name to colour.
            If ``None``, colours are automatically generated from
            :data:`QUALITATIVE_COLORS`.
        point_size: Diameter of the scatter markers in pixels
            (default ``14``). Must be > 0.
        text_position: Position of the recommendation name relative to
            its marker — ``"top center"`` (default), ``"middle right"``,
            ``"bottom center"``, etc.
        show_quadrant_labels: If ``True``, display quadrant names as
            background annotations (default ``True``).
        show_quadrant_backgrounds: If ``True``, tint each quadrant with
            its background colour (default ``True``).
        show_threshold_lines: If ``True``, draw dashed threshold lines
            (default ``True``).
        show_legend: If ``True``, display the category legend
            (default ``True``).
        hover_template: Custom Plotly hover template. If ``None``, a
            rich default is used showing name, impact, effort, and
            category.
        background_color: Plot background colour (default :data:`SURFACE`).
        paper_color: Paper background colour (default :data:`BACKGROUND`).
        title_color: Colour of the title text (default :data:`TEXT_PRIMARY`).
        font_family: Font family for all text (default :data:`DEFAULT_FONT`).
        font_size: Base font size in pixels (default ``14``). Must be > 0.
        width: Figure width in pixels (default ``900``). Must be > 0.
        height: Figure height in pixels (default ``700``). Must be > 0.

    Raises:
        TypeError: If any argument has an invalid type.
        ValueError: If arguments violate business rules (empty data,
            duplicate names, threshold out of range, etc.).

    Example:
        >>> matrix = DecisionMatrix(
        ...     recommendations=[
        ...         Recommendation("Deploy MES", 92, 81, "Technology"),
        ...         Recommendation("Train Staff", 75, 30, "People"),
        ...         Recommendation("Upgrade ERP", 60, 85, "Technology"),
        ...         Recommendation("Audit Process", 40, 25, "Process"),
        ...     ],
        ...     title="Prioritisation Matrix",
        ...     x_threshold=50,
        ...     y_threshold=50,
        ... )
        >>> fig = matrix.create()
    """

    # -- required data -------------------------------------------------
    recommendations: Sequence[Recommendation]

    # -- textual metadata ----------------------------------------------
    title: str = ""

    # -- quadrant configuration ----------------------------------------
    x_threshold: float | int = _DEFAULT_X_THRESHOLD
    y_threshold: float | int = _DEFAULT_Y_THRESHOLD
    quadrant_labels: QuadrantLabels = field(default_factory=QuadrantLabels)
    quadrant_colors: QuadrantColors = field(default_factory=QuadrantColors)

    # -- visual styling ------------------------------------------------
    category_colors: dict[str, str] | None = None
    point_size: int = _DEFAULT_POINT_SIZE
    text_position: str = _DEFAULT_TEXT_POSITION
    show_quadrant_labels: bool = _DEFAULT_SHOW_QUADRANT_LABELS
    show_quadrant_backgrounds: bool = _DEFAULT_SHOW_QUADRANT_BACKGROUNDS
    show_threshold_lines: bool = _DEFAULT_SHOW_THRESHOLD_LINES
    show_legend: bool = _DEFAULT_SHOW_LEGEND
    hover_template: str | None = None

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
        """Build and return the configured decision matrix figure.

        Returns:
            A Plotly :class:`go.Figure` ready for rendering or export.

        Raises:
            TypeError: If any argument has an invalid type.
            ValueError: If data is inconsistent or violates business rules.
        """
        self._validate()
        fig = go.Figure()
        self._build_quadrant_backgrounds(fig)
        self._build_threshold_lines(fig)
        self._build_scatter_traces(fig)
        self._build_quadrant_annotations(fig)
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
        # -- recommendations ---------------------------------------------
        if not isinstance(self.recommendations, Sequence):
            raise TypeError(
                f"recommendations must be a sequence, got {type(self.recommendations).__name__}"
            )
        if len(self.recommendations) == 0:
            raise ValueError("recommendations must not be empty")

        seen_names: set[str] = set()
        for i, rec in enumerate(self.recommendations):
            if not isinstance(rec, Recommendation):
                raise TypeError(
                    f"recommendations[{i}] must be Recommendation, "
                    f"got {type(rec).__name__}"
                )
            if rec.name in seen_names:
                raise ValueError(
                    f"Duplicate recommendation name detected at index {i}: "
                    f"{rec.name!r}. All recommendation names must be unique."
                )
            seen_names.add(rec.name)

        # -- thresholds --------------------------------------------------
        _validate_percentage("x_threshold", self.x_threshold)
        _validate_percentage("y_threshold", self.y_threshold)

        # -- dimensions & font -------------------------------------------
        _validate_positive_int("width", self.width)
        _validate_positive_int("height", self.height)
        _validate_positive_int("font_size", self.font_size)
        _validate_positive_int("point_size", self.point_size)

        # -- string types ------------------------------------------------
        _validate_str("title", self.title)
        _validate_str("text_position", self.text_position)
        _validate_str_or_none("hover_template", self.hover_template)
        _validate_str("font_family", self.font_family)
        _validate_str("background_color", self.background_color)
        _validate_str("paper_color", self.paper_color)
        _validate_str("title_color", self.title_color)

        # -- boolean types -----------------------------------------------
        for name in (
            "show_quadrant_labels",
            "show_quadrant_backgrounds",
            "show_threshold_lines",
            "show_legend",
        ):
            val = getattr(self, name)
            if not isinstance(val, bool):
                raise TypeError(
                    f"{name} must be bool, got {type(val).__name__}"
                )

        # -- category_colors validation ----------------------------------
        if self.category_colors is not None:
            if not isinstance(self.category_colors, dict):
                raise TypeError(
                    f"category_colors must be dict or None, got {type(self.category_colors).__name__}"
                )
            categories = self._extract_categories()
            for cat in categories:
                if cat not in self.category_colors:
                    raise ValueError(
                        f"category_colors is missing an entry for category {cat!r}"
                    )
            for cat, color in self.category_colors.items():
                if not isinstance(color, str):
                    raise TypeError(
                        f"category_colors[{cat!r}] must be str, got {type(color).__name__}"
                    )

        # -- quadrant_labels & quadrant_colors types ---------------------
        if not isinstance(self.quadrant_labels, QuadrantLabels):
            raise TypeError(
                f"quadrant_labels must be QuadrantLabels, got {type(self.quadrant_labels).__name__}"
            )
        if not isinstance(self.quadrant_colors, QuadrantColors):
            raise TypeError(
                f"quadrant_colors must be QuadrantColors, got {type(self.quadrant_colors).__name__}"
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_categories(self) -> list[str]:
        """Return the sorted list of unique category names.

        Returns:
            Sorted list of unique category strings.
        """
        return sorted({rec.category for rec in self.recommendations})

    def _resolve_category_colors(self) -> dict[str, str]:
        """Resolve the colour mapping for all categories.

        Uses custom colours if provided, otherwise generates from
        :data:`QUALITATIVE_COLORS`.

        Returns:
            Dictionary mapping category name to hex colour string.
        """
        if self.category_colors is not None:
            return dict(self.category_colors)
        categories = self._extract_categories()
        colors = generate_colors(QUALITATIVE_COLORS, len(categories))
        return dict(zip(categories, colors))

    def _group_by_category(self) -> dict[str, list[Recommendation]]:
        """Group recommendations by their category.

        Returns:
            Dictionary mapping category name to list of recommendations.
        """
        groups: dict[str, list[Recommendation]] = {}
        for rec in self.recommendations:
            groups.setdefault(rec.category, []).append(rec)
        return groups

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def _build_quadrant_backgrounds(self, fig: go.Figure) -> None:
        """Add semi-transparent background rectangles for each quadrant.

        Args:
            fig: The figure to decorate (mutated in place).
        """
        if not self.show_quadrant_backgrounds:
            return

        x_t = float(self.x_threshold)
        y_t = float(self.y_threshold)

        quadrants = [
            (0, y_t, x_t, 100, self.quadrant_colors.quick_wins),      # top-left
            (x_t, y_t, 100, 100, self.quadrant_colors.strategic),      # top-right
            (0, 0, x_t, y_t, self.quadrant_colors.low_priority),       # bottom-left
            (x_t, 0, 100, y_t, self.quadrant_colors.avoid),            # bottom-right
        ]

        for x0, y0, x1, y1, fillcolor in quadrants:
            fig.add_shape(
                type="rect",
                x0=x0,
                y0=y0,
                x1=x1,
                y1=y1,
                fillcolor=fillcolor,
                line_width=0,
                layer="below",
            )

    def _build_threshold_lines(self, fig: go.Figure) -> None:
        """Add dashed threshold lines to separate quadrants.

        Args:
            fig: The figure to decorate (mutated in place).
        """
        if not self.show_threshold_lines:
            return

        fig.add_hline(
            y=float(self.y_threshold),
            line_dash="dash",
            line_color=BORDER,
            line_width=2,
            layer="above",
        )
        fig.add_vline(
            x=float(self.x_threshold),
            line_dash="dash",
            line_color=BORDER,
            line_width=2,
            layer="above",
        )

    def _build_scatter_traces(self, fig: go.Figure) -> None:
        """Add one Scatter trace per category.

        Args:
            fig: The figure to populate (mutated in place).
        """
        groups = self._group_by_category()
        colors = self._resolve_category_colors()

        default_hover = (
            "<b>%{customdata[0]}</b><br>"
            "Impact: %{y:.1f}<br>"
            "Effort: %{x:.1f}<br>"
            "Category: %{customdata[1]}<extra></extra>"
        )
        hovertemplate = self.hover_template if self.hover_template is not None else default_hover

        for category in sorted(groups.keys()):
            recs = groups[category]
            color = colors[category]

            fig.add_trace(go.Scatter(
                x=[rec.effort for rec in recs],
                y=[rec.impact for rec in recs],
                mode="markers+text",
                name=category,
                text=[rec.name for rec in recs],
                textposition=self.text_position,
                marker=dict(
                    size=self.point_size,
                    color=color,
                    line=dict(color=TEXT_PRIMARY, width=1),
                    symbol="circle",
                ),
                textfont=dict(
                    family=self.font_family,
                    size=self.font_size - 1,
                    color=TEXT_PRIMARY,
                ),
                customdata=[[rec.name, rec.category] for rec in recs],
                hovertemplate=hovertemplate,
            ))

    def _build_quadrant_annotations(self, fig: go.Figure) -> None:
        """Add quadrant name annotations at the centre of each zone.

        Args:
            fig: The figure to annotate (mutated in place).
        """
        if not self.show_quadrant_labels:
            return

        x_t = float(self.x_threshold)
        y_t = float(self.y_threshold)

        annotations = [
            (x_t / 2, (100 + y_t) / 2, self.quadrant_labels.quick_wins),
            ((100 + x_t) / 2, (100 + y_t) / 2, self.quadrant_labels.strategic),
            (x_t / 2, y_t / 2, self.quadrant_labels.low_priority),
            ((100 + x_t) / 2, y_t / 2, self.quadrant_labels.avoid),
        ]

        for x, y, text in annotations:
            fig.add_annotation(
                x=x,
                y=y,
                text=f"<b>{text}</b>",
                showarrow=False,
                font=dict(
                    family=self.font_family,
                    size=self.font_size + 2,
                    color=TEXT_SECONDARY,
                ),
                opacity=0.35,
                xref="x",
                yref="y",
            )

    def _build_layout(self, fig: go.Figure) -> None:
        """Apply decision-matrix-specific layout styling.

        Args:
            fig: The figure to style (mutated in place).
        """
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
            showlegend=self.show_legend,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(
                    family=self.font_family,
                    size=self.font_size,
                    color=TEXT_SECONDARY,
                ),
            ),
            margin=dict(l=60, r=60, t=80, b=80),
            xaxis=dict(
                title="Effort →",
                range=[_DEFAULT_MIN_EFFORT, _DEFAULT_MAX_EFFORT],
                showgrid=True,
                gridcolor=GRID,
                zeroline=False,
                linecolor=BORDER,
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
            ),
            yaxis=dict(
                title="Impact →",
                range=[_DEFAULT_MIN_IMPACT, _DEFAULT_MAX_IMPACT],
                showgrid=True,
                gridcolor=GRID,
                zeroline=False,
                linecolor=BORDER,
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
                scaleanchor="x",
                scaleratio=1,
            ),
            hoverlabel=dict(
                font=dict(family=self.font_family, size=self.font_size),
                bgcolor=BACKGROUND,
                bordercolor=PRIMARY,
            ),
        )