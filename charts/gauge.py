"""Gauge chart component for the JESA DMAT visualization package.

Provides a professional, industrial-grade gauge chart built on Plotly's
``indicator`` trace with configurable ranges, threshold markers, and
Industry-5.0 inspired default styling.

All colors are sourced from :mod:`charts.palette` to maintain visual
consistency across the application.

Usage::

    from charts.gauge_chart import GaugeChart

    gauge = GaugeChart(value=72.5, title="Digital Maturity Score")
    fig = gauge.create()
    fig.show()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

import plotly.graph_objects as go

from charts.palette import (
    BACKGROUND,
    BORDER,
    PRIMARY,
    TEXT_SECONDARY,
    SURFACE,
    TEXT_PRIMARY,
)

__all__ = ["GaugeChart"]

# ---------------------------------------------------------------------------
# Default gauge steps (Industry 5.0 inspired)
# ---------------------------------------------------------------------------
_DEFAULT_STEPS: tuple[tuple[float, float, str], ...] = (
    (0.0, 40.0, "#EF4444"),   # Red – Low
    (40.0, 70.0, "#F59E0B"),  # Orange – Medium
    (70.0, 100.0, "#10B981"), # Green – High
)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
_DEFAULT_BAR_COLOR: str = PRIMARY
_DEFAULT_BACKGROUND_COLOR: str = SURFACE
_DEFAULT_PAPER_COLOR: str = BACKGROUND
_DEFAULT_TITLE_COLOR: str = TEXT_PRIMARY
_DEFAULT_FONT_FAMILY: str = "Inter"
_DEFAULT_FONT_SIZE: int = 14
_DEFAULT_HEIGHT: int = 350
_DEFAULT_DOMAIN: dict[str, list[float]] = {"x": [0.0, 1.0], "y": [0.0, 1.0]}


# ---------------------------------------------------------------------------
# Private validation helpers
# ---------------------------------------------------------------------------


def _validate_str(name: str, value: object) -> None:
    """Raise TypeError if ``value`` is not a string."""
    if not isinstance(value, str):
        raise TypeError(
            f"{name} must be str, got {type(value).__name__}"
        )


# =============================================================================
# GaugeChart
# =============================================================================


@dataclass
class GaugeChart:
    """Industrial-grade gauge chart for maturity scores and KPIs.

    Encapsulates all configuration needed to render a Plotly gauge
    indicator. Call :meth:`create` to obtain the final ``go.Figure``.

    Args:
        value: Current gauge value (must be within ``[min_value, max_value]``).
        title: Chart title displayed above the gauge.
        min_value: Minimum scale value (default ``0``).
        max_value: Maximum scale value (default ``100``).
        unit: Unit label appended to the displayed value (default ``"%"``).
        height: Figure height in pixels (default ``350``). Must be > 0.
        width: Optional figure width in pixels. Must be > 0 if provided.
        show_value: If ``True``, display the numeric value (default ``True``).
        show_threshold: If ``True``, display a threshold marker (default ``True``).
        threshold: Optional threshold value for the marker line.
        reference_value: Optional reference value (e.g. target, benchmark,
            previous score). When provided, Plotly displays a ``+N`` or ``-N``
            delta relative to this reference. Must be within gauge bounds.
        shape: Gauge shape – ``"angular"`` (default) or ``"bullet"``.
        value_format: Plotly format string for the displayed numeric value
            (default ``".1f"``). Uses d3-format syntax.
        steps: Optional gauge range definitions. Each tuple is
            ``(start, end, color)``. Must cover the full ``[min_value, max_value]``
            range without gaps or overlaps. If ``None``, Industry-5.0 defaults
            are used.
        bar_color: Color of the gauge bar (default :data:`PRIMARY`).
        background_color: Plot background color (default :data:`SURFACE`).
        paper_color: Paper background color (default :data:`BACKGROUND`).
        title_color: Title text color (default :data:`TEXT_PRIMARY`).
        font_family: Font family for all text (default ``"Inter"``).
        font_size: Base font size (default ``14``). Must be > 0.

    Example:
        >>> gauge = GaugeChart(value=72, reference_value=65, title="Score")
        >>> fig = gauge.create()
    """

    value: float
    title: str = ""
    min_value: float = 0.0
    max_value: float = 100.0
    unit: str = "%"
    height: int = _DEFAULT_HEIGHT
    width: int | None = None
    show_value: bool = True
    show_threshold: bool = True
    threshold: float | None = None
    reference_value: float | None = None
    shape: Literal["angular", "bullet"] = "angular"
    value_format: str = ".1f"
    steps: Sequence[tuple[float, float, str]] | None = None
    bar_color: str = _DEFAULT_BAR_COLOR
    background_color: str = _DEFAULT_BACKGROUND_COLOR
    paper_color: str = _DEFAULT_PAPER_COLOR
    title_color: str = _DEFAULT_TITLE_COLOR
    font_family: str = _DEFAULT_FONT_FAMILY
    font_size: int = _DEFAULT_FONT_SIZE

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self) -> go.Figure:
        """Build and return the configured gauge figure.

        Returns:
            A Plotly :class:`go.Figure` ready for rendering or export.

        Raises:
            TypeError: If any argument has an invalid type.
            ValueError: If values are out of range or steps are invalid.
        """
        self._validate()
        resolved_steps = self._build_steps()
        indicator = self._build_indicator(resolved_steps)
        fig = go.Figure(data=[indicator])
        self._build_layout(fig)
        return fig

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate(self) -> None:
        """Validate all constructor arguments.

        Raises:
            TypeError: If a parameter has an incorrect type.
            ValueError: If a parameter is out of its allowed range or
                steps are invalid.
        """
        # -- numeric values (direct validation) --------------------------
        for name, val in [
            ("value", self.value),
            ("min_value", self.min_value),
            ("max_value", self.max_value),
        ]:
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise TypeError(
                    f"{name} must be a number, got {type(val).__name__}"
                )

        # -- range logic -------------------------------------------------
        if self.min_value >= self.max_value:
            raise ValueError(
                f"min_value ({self.min_value}) must be < max_value ({self.max_value})"
            )
        if not self.min_value <= self.value <= self.max_value:
            raise ValueError(
                f"value ({self.value}) must be between "
                f"min_value ({self.min_value}) and max_value ({self.max_value})"
            )

        # -- threshold ---------------------------------------------------
        if self.threshold is not None:
            if not isinstance(self.threshold, (int, float)) or isinstance(self.threshold, bool):
                raise TypeError(
                    f"threshold must be a number, got {type(self.threshold).__name__}"
                )
            if not self.min_value <= self.threshold <= self.max_value:
                raise ValueError(
                    f"threshold ({self.threshold}) must be between "
                    f"min_value ({self.min_value}) and max_value ({self.max_value})"
                )

        # -- reference ---------------------------------------------------
        if self.reference_value is not None:
            if not isinstance(self.reference_value, (int, float)) or isinstance(self.reference_value, bool):
                raise TypeError(
                    f"reference_value must be a number, "
                    f"got {type(self.reference_value).__name__}"
                )
            if not self.min_value <= self.reference_value <= self.max_value:
                raise ValueError(
                    f"reference_value ({self.reference_value}) must be between "
                    f"min_value ({self.min_value}) and max_value ({self.max_value})"
                )

        # -- dimensions & font -------------------------------------------
        for name, val in [("height", self.height), ("font_size", self.font_size)]:
            if not isinstance(val, int) or isinstance(val, bool):
                raise TypeError(
                    f"{name} must be int, got {type(val).__name__}"
                )
            if val <= 0:
                raise ValueError(f"{name} must be > 0, got {val}")
        if self.width is not None:
            if not isinstance(self.width, int) or isinstance(self.width, bool):
                raise TypeError(
                    f"width must be int, got {type(self.width).__name__}"
                )
            if self.width <= 0:
                raise ValueError(f"width must be > 0, got {self.width}")

        # -- string types ------------------------------------------------
        _validate_str("title", self.title)
        _validate_str("unit", self.unit)
        _validate_str("font_family", self.font_family)
        _validate_str("value_format", self.value_format)

        # -- shape -------------------------------------------------------
        if self.shape not in ("angular", "bullet"):
            raise ValueError(
                f"shape must be 'angular' or 'bullet', got {self.shape!r}"
            )

        # -- boolean types -----------------------------------------------
        if not isinstance(self.show_value, bool):
            raise TypeError(
                f"show_value must be bool, got {type(self.show_value).__name__}"
            )
        if not isinstance(self.show_threshold, bool):
            raise TypeError(
                f"show_threshold must be bool, got {type(self.show_threshold).__name__}"
            )

        # -- steps -------------------------------------------------------
        if self.steps is not None:
            self._validate_steps(self.steps)

    def _validate_steps(
        self, steps: Sequence[tuple[float, float, str]]
    ) -> None:
        """Validate the user-provided gauge steps.

        Steps must:
        * Cover the full ``[min_value, max_value]`` range.
        * Be non-overlapping and sorted.
        * Have valid types for start, end, and color.

        Args:
            steps: List of ``(start, end, color)`` tuples.

        Raises:
            TypeError: If ``steps`` is not a sequence of valid tuples.
            ValueError: If steps are incomplete, overlapping, or out of bounds.
        """
        if len(steps) == 0:
            raise ValueError("steps must not be empty")

        for i, step in enumerate(steps):
            if not isinstance(step, tuple) or len(step) != 3:
                raise TypeError(
                    f"steps[{i}] must be a tuple of (start, end, color), "
                    f"got {step!r}"
                )
            start, end, color = step
            if not isinstance(start, (int, float)) or isinstance(start, bool):
                raise TypeError(
                    f"steps[{i}] start must be a number, "
                    f"got {type(start).__name__}"
                )
            if not isinstance(end, (int, float)) or isinstance(end, bool):
                raise TypeError(
                    f"steps[{i}] end must be a number, "
                    f"got {type(end).__name__}"
                )
            if not isinstance(color, str):
                raise TypeError(
                    f"steps[{i}] color must be str, got {type(color).__name__}"
                )
            if start >= end:
                raise ValueError(
                    f"steps[{i}] start ({start}) must be < end ({end})"
                )
            if start < self.min_value or end > self.max_value:
                raise ValueError(
                    f"steps[{i}] [{start}, {end}] is outside gauge bounds "
                    f"[{self.min_value}, {self.max_value}]"
                )
            if i > 0:
                prev_end = steps[i - 1][1]
                if start != prev_end:
                    raise ValueError(
                        f"steps[{i}] start ({start}) must equal previous "
                        f"step end ({prev_end}). No gaps allowed."
                    )

        # First step must start at min_value
        if steps[0][0] != self.min_value:
            raise ValueError(
                f"First step start ({steps[0][0]}) must equal "
                f"min_value ({self.min_value})"
            )
        # Last step must end at max_value
        if steps[-1][1] != self.max_value:
            raise ValueError(
                f"Last step end ({steps[-1][1]}) must equal "
                f"max_value ({self.max_value})"
            )

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def _build_steps(self) -> list[dict[str, object]]:
        """Return the gauge steps in Plotly format.

        Returns:
            List of step dictionaries with ``range`` and ``color`` keys.
        """
        source = self.steps if self.steps is not None else _DEFAULT_STEPS
        return [
            {"range": [start, end], "color": color}
            for start, end, color in source
        ]

    def _build_threshold(self) -> dict[str, object] | None:
        """Return the threshold configuration for Plotly.

        Returns:
            Threshold dictionary or ``None`` if ``show_threshold`` is
            ``False`` or no threshold is set.
        """
        if not self.show_threshold or self.threshold is None:
            return None
        return {
            "line": {"color": "black", "width": 2},
            "thickness": 0.08,
            "value": self.threshold,
        }

    def _build_indicator(
        self, steps: list[dict[str, object]]
    ) -> go.Indicator:
        """Build the Plotly indicator trace.

        Args:
            steps: Formatted gauge steps.

        Returns:
            Configured :class:`go.Indicator`.
        """
        mode = "gauge"
        if self.show_value:
            mode += "+number"
        if self.reference_value is not None:
            mode += "+delta"

        number_config: dict[str, object] = {}
        if self.show_value:
            number_config = {
                "suffix": f" {self.unit}",
                "valueformat": self.value_format,
            }

        delta_config: dict[str, object] = {}
        if self.reference_value is not None:
            delta_config = {
                "reference": self.reference_value,
                "increasing": {"color": "#10B981"},
                "decreasing": {"color": "#EF4444"},
            }

        return go.Indicator(
            mode=mode,
            value=self.value,
            title={"text": self.title, "font": {"color": self.title_color}},
            number=number_config,
            delta=delta_config if self.reference_value is not None else {},
            domain=_DEFAULT_DOMAIN,
            gauge={
                "shape": self.shape,
                "axis": {
                    "range": [self.min_value, self.max_value],
                    "tickwidth": 1,
                    "tickcolor": BORDER,
                    "tickfont": {"size": 12, "color": TEXT_SECONDARY},
                },
                "bar": {"color": self.bar_color},
                "steps": steps,
                "threshold": self._build_threshold(),
                "bgcolor": "rgba(0,0,0,0)",
            },
        )

    def _build_layout(self, fig: go.Figure) -> None:
        """Apply layout styling to the figure.

        Args:
            fig: The figure to style (mutated in place).
        """
        fig.update_layout(
            height=self.height,
            width=self.width,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor=self.paper_color,
            plot_bgcolor=self.background_color,
            font=dict(
                family=self.font_family,
                size=self.font_size,
                color=self.title_color,
            ),
        )
