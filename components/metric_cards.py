# JESA_DMAT/components/metric_cards.py

"""
Specialized metric components for the JESA DMAT Dashboard.

This module provides UI components for displaying key digital maturity
indicators, such as the overall maturity score, pillar scores,
and performance trends.

These components are intended for the Dashboard and analysis pages,
and use the JESA DMAT design system.

They differ from the generic components in `cards.py` because they are
specifically designed for maturity metrics (score, level, trend).

Typical usage:

from components.metric_cards import (
    render_maturity_metric,
    render_pillar_metric,
    render_trend_metric,
)

render_maturity_metric(
    label="Overall Maturity",
    value=72,
    unit="%",
    level="Advanced",
    icon="📊",
    precision=1,
)

render_pillar_metric(
    label="Infrastructure",
    value=85,
    unit="%",
    status="success",
    icon="🏭",
)

render_trend_metric(
    label="Progression",
    value=72,
    unit="%",
    delta="+5%",
    trend="positive",
    icon="📈",
)
"""

from __future__ import annotations

from html import escape
from typing import Any, Optional

import streamlit as st


# ============================================================================
# CONSTANTS
# ============================================================================

_STATUS_MAP = {
    "success": "positive",
    "positive": "positive",
    "advanced": "positive",
    "high": "positive",
    "warning": "warning",
    "medium": "warning",
    "danger": "negative",
    "negative": "negative",
    "low": "negative",
    "neutral": "neutral",
}


# ============================================================================
# INTERNAL HELPERS
# ============================================================================

def _render_html(html: str) -> None:
    """Render trusted HTML through Streamlit."""
    st.markdown(html, unsafe_allow_html=True)


def _map_status_to_metric(status: Optional[str]) -> Optional[str]:
    """
    Convert a semantic status into a metric CSS class.

    Args:
        status: Semantic status, e.g. "success", "advanced", "high".

    Returns:
        The corresponding metric class ("positive", "warning",
        "negative", "neutral"), or None.
    """
    if status is None:
        return None

    normalized = str(status).strip().lower()
    return _STATUS_MAP.get(normalized, normalized)


def _format_number(value: Any, decimals: Optional[int] = None) -> str:
    """
    Format a numeric value for display.

    Args:
        value: Value to format (int, float, or another type).
        decimals: Number of decimal places to display. If None,
            uses the `:g` format to remove unnecessary trailing zeros.

    Returns:
        Formatted string.
    """
    if isinstance(value, (int, float)):
        if decimals is not None:
            return f"{value:.{decimals}f}"

        return f"{value:g}"

    return str(value)


def _build_metric_classes(status: Optional[str] = None) -> str:
    """
    Build the CSS class string for a metric.

    Args:
        status: Semantic status, which will be mapped to a metric class.

    Returns:
        CSS class string.
    """
    classes = ["dmat-metric"]

    mapped = _map_status_to_metric(status)

    if mapped:
        classes.append(f"dmat-metric--{mapped}")

    return " ".join(classes)


# ============================================================================
# PUBLIC COMPONENTS
# ============================================================================

def render_maturity_metric(
    label: str,
    value: float | int,
    unit: Optional[str] = None,
    level: Optional[str] = None,
    icon: Optional[str] = None,
    status: Optional[str] = None,
    precision: Optional[int] = None,
    **kwargs: Any,
) -> None:
    """
    Display an overall maturity metric with a textual maturity level.

    Args:
        label: Metric label.
        value: Numeric maturity score.
        unit: Unit, e.g. "%". A space is automatically added.
        level: Textual maturity level, e.g. "Advanced".
        icon: Icon (emoji or HTML) displayed with the metric.
        status: Semantic status mapped to the metric CSS style.
        precision: Number of decimal places to display.
        **kwargs: Additional arguments ignored for future extensibility.

    Returns:
        None

    Example:

        render_maturity_metric(
            label="Overall Maturity",
            value=72.4,
            unit="%",
            level="Advanced",
            status="success",
            icon="📊",
            precision=1,
        )
    """

    # Escape user-provided values
    escaped_label = escape(str(label))
    escaped_value = escape(_format_number(value, precision))
    escaped_level = escape(str(level)) if level is not None else None
    escaped_icon = escape(str(icon)) if icon is not None else None

    # Add unit
    if unit:
        escaped_value += f" {unit}"

    classes = _build_metric_classes(status)

    html_parts = [
        f'<div class="{classes}">'
    ]

    # Icon
    if escaped_icon:
        html_parts.append(
            f'<div class="dmat-metric__icon">{escaped_icon}</div>'
        )

    # Label
    html_parts.append(
        f'<div class="dmat-metric__label">{escaped_label}</div>'
    )

    # Value
    html_parts.append(
        f'<div class="dmat-metric__value">{escaped_value}</div>'
    )

    # Maturity level
    if escaped_level:
        html_parts.append(
            f'<div class="dmat-metric__level">{escaped_level}</div>'
        )

    html_parts.append("</div>")

    _render_html("\n".join(html_parts))


def render_pillar_metric(
    label: str,
    value: float | int,
    unit: Optional[str] = None,
    icon: Optional[str] = None,
    status: Optional[str] = None,
    precision: Optional[int] = None,
    **kwargs: Any,
) -> None:
    """
    Display a maturity metric for a digital transformation pillar.

    Args:
        label: Pillar label.
        value: Pillar score.
        unit: Unit, e.g. "%".
        icon: Icon (emoji or HTML) displayed with the metric.
        status: Semantic status mapped to the metric CSS style.
        precision: Number of decimal places to display.
        **kwargs: Additional arguments ignored for future extensibility.

    Returns:
        None

    Example:

        render_pillar_metric(
            label="Infrastructure",
            value=85,
            unit="%",
            status="success",
            icon="🏭",
        )
    """

    # Escape user-provided values
    escaped_label = escape(str(label))
    escaped_value = escape(_format_number(value, precision))
    escaped_icon = escape(str(icon)) if icon is not None else None

    # Add unit
    if unit:
        escaped_value += f" {unit}"

    classes = _build_metric_classes(status)

    html_parts = [
        f'<div class="{classes}">'
    ]

    # Icon
    if escaped_icon:
        html_parts.append(
            f'<div class="dmat-metric__icon">{escaped_icon}</div>'
        )

    # Label
    html_parts.append(
        f'<div class="dmat-metric__label">{escaped_label}</div>'
    )

    # Value
    html_parts.append(
        f'<div class="dmat-metric__value">{escaped_value}</div>'
    )

    html_parts.append("</div>")

    _render_html("\n".join(html_parts))


def render_trend_metric(
    label: str,
    value: float | int,
    unit: Optional[str] = None,
    delta: Optional[str] = None,
    trend: Optional[str] = None,
    icon: Optional[str] = None,
    precision: Optional[int] = None,
    **kwargs: Any,
) -> None:
    """
    Display a metric with a performance trend and delta.

    Args:
        label: Metric label.
        value: Current value.
        unit: Unit, e.g. "%".
        delta: Variation text, e.g. "+5%" or "-2".
        trend: Semantic trend ("positive", "negative", "neutral",
            "success", "warning", etc.). It will be mapped to
            the corresponding metric CSS class.
        icon: Icon (emoji or HTML) displayed with the metric.
        precision: Number of decimal places to display.
        **kwargs: Additional arguments ignored for future extensibility.

    Returns:
        None

    Example:

        render_trend_metric(
            label="Progress",
            value=72,
            unit="%",
            delta="+5%",
            trend="positive",
            icon="📈",
            precision=1,
        )
    """

    # Escape user-provided values
    escaped_label = escape(str(label))
    escaped_value = escape(_format_number(value, precision))
    escaped_delta = escape(str(delta)) if delta is not None else None
    escaped_icon = escape(str(icon)) if icon is not None else None

    # Add unit
    if unit:
        escaped_value += f" {unit}"

    classes = _build_metric_classes(trend)

    html_parts = [
        f'<div class="{classes}">'
    ]

    # Icon
    if escaped_icon:
        html_parts.append(
            f'<div class="dmat-metric__icon">{escaped_icon}</div>'
        )

    # Label
    html_parts.append(
        f'<div class="dmat-metric__label">{escaped_label}</div>'
    )

    # Value
    html_parts.append(
        f'<div class="dmat-metric__value">{escaped_value}</div>'
    )

    # Delta
    if escaped_delta:
        html_parts.append(
            f'<div class="dmat-metric__delta">{escaped_delta}</div>'
        )

    html_parts.append("</div>")

    _render_html("\n".join(html_parts))


# ============================================================================
# PUBLIC EXPORTS
# ============================================================================

__all__ = [
    "render_maturity_metric",
    "render_pillar_metric",
    "render_trend_metric",
]