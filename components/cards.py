# JESA_DMAT/components/cards.py

"""
Reusable UI card components for the JESA DMAT Streamlit frontend.

This module provides presentation-only card components based on the
JESA DMAT design system.

The components:
    - contain no business logic;
    - do not import engines, services, or data-processing modules;
    - escape dynamic text before injecting it into HTML;
    - rely on CSS classes defined in the frontend assets.

Typical usage:

    from components.cards import render_card, render_metric_card

    render_card(
        title="Maturité Globale",
        value="72 %",
        subtitle="Score consolidé",
        description="Évaluation globale de la maturité digitale.",
        status="success",
        icon="📊",
    )

    render_metric_card(
        label="Infrastructure",
        value=85,
        unit="%",
        delta="+5%",
        status="positive",
    )

    render_card(
        title="Action requise",
        description="Mettez à jour votre profil.",
        status="warning",
        children=lambda: st.button("Mettre à jour"),
    )
"""

from __future__ import annotations

import re
from html import escape
from typing import Any, Callable, Optional

import streamlit as st


# ============================================================================
# STATUS MAPPING
# ============================================================================

_STATUS_MAP: dict[str, str] = {
    "success": "success",
    "warning": "warning",
    "danger": "danger",
    "neutral": "neutral",
    "advanced": "success",
    "high": "success",
    "medium": "warning",
    "low": "danger",
}


# ============================================================================
# INTERNAL HELPERS
# ============================================================================


def _map_status(status: Optional[str]) -> Optional[str]:
    """Map a semantic status to a CSS-compatible status."""
    if status is None:
        return None

    normalized = str(status).strip().lower()

    if not normalized:
        return None

    return _STATUS_MAP.get(normalized, normalized)


def _sanitize_css_token(value: str) -> str:
    """
    Keep only characters suitable for a CSS class token.

    This prevents accidental malformed class names when a custom
    variant is supplied.
    """
    return re.sub(r"[^a-zA-Z0-9_-]", "", value.strip())


def _build_card_classes(
    *,
    status: Optional[str] = None,
    variant: Optional[str] = None,
    compact: bool = False,
    highlighted: bool = False,
) -> str:
    """Build the CSS class list for a generic card."""

    classes = ["dmat-card"]

    if compact:
        classes.append("dmat-card--compact")

    if highlighted:
        classes.append("dmat-card--highlighted")

    if variant:
        safe_variant = _sanitize_css_token(variant)

        if safe_variant:
            classes.append(f"dmat-card--{safe_variant}")

    mapped_status = _map_status(status)

    if mapped_status:
        safe_status = _sanitize_css_token(mapped_status)

        if safe_status:
            classes.append(f"dmat-status--{safe_status}")

    return " ".join(classes)


def _render_html(html: str) -> None:
    """
    Render trusted component HTML.

    Dynamic textual values are escaped before reaching this helper.
    """
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# GENERIC CARD
# ============================================================================


def render_card(
    title: Optional[str] = None,
    value: Optional[str] = None,
    subtitle: Optional[str] = None,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    status: Optional[str] = None,
    variant: Optional[str] = None,
    action: Optional[str] = None,
    children: Optional[Callable[[], Any]] = None,
    compact: bool = False,
    highlighted: bool = False,
    **kwargs: Any,
) -> None:
    """
    Render a reusable JESA DMAT card.

    Args:
        title:
            Main title displayed in the card header.

        value:
            Main highlighted value.

        subtitle:
            Secondary text displayed below the value.

        description:
            Descriptive text displayed below the subtitle.

        icon:
            Optional icon or emoji.

        status:
            Semantic status such as:
            ``success``, ``warning``, ``danger``, ``neutral``,
            ``advanced``, ``high``, ``medium`` or ``low``.

        variant:
            Optional CSS card variant.

        action:
            Optional decorative action text displayed in the footer.
            For interactive Streamlit widgets, prefer ``children``.

        children:
            Optional callable used to render additional Streamlit widgets
            after the card HTML.

            Example:
                children=lambda: st.button("Mettre à jour")

        compact:
            Apply the compact card style.

        highlighted:
            Apply the highlighted card style.

        **kwargs:
            Reserved for future extensibility.

    Returns:
        None
    """

    classes = _build_card_classes(
        status=status,
        variant=variant,
        compact=compact,
        highlighted=highlighted,
    )

    html_parts: list[str] = [
        f'<div class="{escape(classes, quote=True)}">'
    ]

    # ------------------------------------------------------------------
    # HEADER
    # ------------------------------------------------------------------

    if title is not None or icon is not None:
        header_parts: list[str] = []

        if icon is not None:
            header_parts.append(
                f'<span class="dmat-card__icon">'
                f"{escape(str(icon))}"
                f"</span>"
            )

        if title is not None:
            header_parts.append(
                f'<span class="dmat-card-title">'
                f"{escape(str(title))}"
                f"</span>"
            )

        html_parts.append(
            '<div class="dmat-card__header">'
            f'{" ".join(header_parts)}'
            "</div>"
        )

    # ------------------------------------------------------------------
    # BODY
    # ------------------------------------------------------------------

    html_parts.append('<div class="dmat-card__body">')

    if value is not None:
        html_parts.append(
            f'<div class="dmat-card-value">'
            f"{escape(str(value))}"
            f"</div>"
        )

    if subtitle is not None:
        html_parts.append(
            f'<div class="dmat-card-subtitle">'
            f"{escape(str(subtitle))}"
            f"</div>"
        )

    if description is not None:
        html_parts.append(
            f'<div class="dmat-card-subtitle dmat-card-description">'
            f"{escape(str(description))}"
            f"</div>"
        )

    html_parts.append("</div>")

    # ------------------------------------------------------------------
    # FOOTER
    # ------------------------------------------------------------------

    if action is not None:
        html_parts.append(
            '<div class="dmat-card__footer">'
            '<span class="dmat-card__action">'
            f"{escape(str(action))}"
            "</span>"
            "</div>"
        )

    # ------------------------------------------------------------------
    # CLOSE CARD
    # ------------------------------------------------------------------

    html_parts.append("</div>")

    # Render the complete HTML card in one Streamlit element.
    _render_html("\n".join(html_parts))

    # Render Streamlit widgets separately.
    if children is not None:
        children()


# ============================================================================
# METRIC CARD
# ============================================================================


def render_metric_card(
    label: str,
    value: float | int,
    unit: Optional[str] = None,
    delta: Optional[str] = None,
    icon: Optional[str] = None,
    status: Optional[str] = None,
    variant: str = "neutral",
    **kwargs: Any,
) -> None:
    """
    Render a compact KPI / metric card.

    Args:
        label:
            Metric label.

        value:
            Numeric metric value.

        unit:
            Optional unit such as ``%``, ``points`` or ``/5``.

        delta:
            Optional variation such as ``+5%`` or ``-2 points``.

        icon:
            Optional icon or emoji.

        status:
            Optional metric status such as ``positive``, ``negative``,
            ``warning`` or ``neutral``.

        variant:
            Default visual variant.

        **kwargs:
            Reserved for future extensibility.

    Returns:
        None
    """

    # Status takes precedence over variant.
    metric_variant = status or variant

    safe_variant = _sanitize_css_token(str(metric_variant).lower())

    classes = ["dmat-metric"]

    if safe_variant:
        classes.append(f"dmat-metric--{safe_variant}")

    class_str = " ".join(classes)

    # Avoid unnecessary decimal places.
    if isinstance(value, float):
        value_str = f"{value:g}"
    else:
        value_str = str(value)

    icon_html = ""

    if icon is not None:
        icon_html = (
            '<div class="dmat-metric__icon">'
            f"{escape(str(icon))}"
            "</div>"
        )

    unit_html = ""

    if unit is not None:
        unit_html = (
            '<span class="dmat-metric__unit">'
            f"{escape(str(unit))}"
            "</span>"
        )

    delta_html = ""

    if delta is not None:
        delta_html = (
            '<div class="dmat-metric__delta">'
            f"{escape(str(delta))}"
            "</div>"
        )

    html = f"""
<div class="{escape(class_str, quote=True)}">
    {icon_html}
    <div class="dmat-metric__label">
        {escape(str(label))}
    </div>
    <div class="dmat-metric__value">
        {escape(value_str)}
        {unit_html}
    </div>
    {delta_html}
</div>
"""

    _render_html(html)


# ============================================================================
# PUBLIC API
# ============================================================================


__all__ = [
    "render_card",
    "render_metric_card",
]