# JESA_DMAT/components/header.py

"""
Reusable page header component for JESA DMAT.

This module provides a function to display a professional
header in Streamlit pages, using the existing design system.

Typical usage:

    from components.header import render_header

    render_header(
        title="Digital Maturity Assessment",
        subtitle="Assessment of your industrial site's digital maturity",
        eyebrow="ASSESSMENT",
        icon="📊",
    )

The component uses the existing CSS classes of the project.
For finer control, you can extend the CSS with the documented classes
below.
"""

from __future__ import annotations

from html import escape
from typing import Any, Optional

import streamlit as st

# ============================================================================
# CONSTANTS
# ============================================================================

_STATUS_MAP = {
    "success": "success",
    "warning": "warning",
    "danger": "danger",
    "neutral": "neutral",
    "advanced": "success",
    "high": "success",
    "medium": "warning",
    "low": "danger",
}

_VALID_ALIGNMENTS = {"left", "center", "right"}

# ============================================================================
# INTERNAL HELPERS
# ============================================================================


def _render_html(html: str) -> None:
    """Render trusted HTML through Streamlit."""
    st.markdown(html, unsafe_allow_html=True)


def _map_status(status: Optional[str]) -> Optional[str]:
    """
    Convert a semantic status into a CSS status class.

    Args:
        status: Semantic status, e.g. "success", "advanced", "high".

    Returns:
        The corresponding CSS class or None.
    """
    if status is None:
        return None

    normalized = str(status).strip().lower()
    return _STATUS_MAP.get(normalized, normalized)


def _build_container_classes(
    align: str = "left",
    compact: bool = False,
) -> str:
    """
    Build the CSS class string for the header container.

    Args:
        align: Content alignment ("left", "center", "right").
        compact: If True, applies a compact style.

    Returns:
        A string containing the CSS classes.
    """
    classes = ["dmat-header"]

    # Alignment classes (defined in utilities.css)
    if align == "left":
        classes.append("u-text-left")
    elif align == "center":
        classes.append("u-text-center")
    elif align == "right":
        classes.append("u-text-right")

    if compact:
        classes.append("dmat-header--compact")

    return " ".join(classes)


# ============================================================================
# MAIN FUNCTION
# ============================================================================


def render_header(
    title: str,
    subtitle: Optional[str] = None,
    eyebrow: Optional[str] = None,
    icon: Optional[str] = None,
    status: Optional[str] = None,
    align: str = "left",
    compact: bool = False,
    **kwargs: Any,
) -> None:
    """
    Display a professional page header.

    Args:
        title (str): Required main title.
        subtitle (str, optional): Subtitle displayed below the title.
        eyebrow (str, optional): Short text displayed above the title
            (e.g. "ASSESSMENT").
        icon (str, optional): Icon (emoji or HTML) displayed next to the title.
        status (str, optional): Semantic status. Possible values:
            "success", "warning", "danger", "neutral",
            "advanced", "high", "medium", "low".
            It will be mapped to a CSS status class.
        align (str): Content alignment. "left", "center", or "right".
            Defaults to "left".
        compact (bool): If True, reduces vertical spacing.
        **kwargs: Additional arguments ignored for future extensibility.

    Returns:
        None

    Raises:
        ValueError: If the alignment is not one of
            ["left", "center", "right"].

    Examples:
        >>> render_header(title="Digital Maturity Assessment")

        >>> render_header(
        ...     title="Digital Maturity Diagnostic",
        ...     subtitle="Assess the current level of digital maturity.",
        ...     eyebrow="ASSESSMENT",
        ...     icon="📊",
        ... )

        >>> render_header(
        ...     title="Decision Analysis",
        ...     subtitle="Identify transformation priorities.",
        ...     eyebrow="DECISION ANALYSIS",
        ...     icon="🎯",
        ...     status="warning",
        ... )

        >>> render_header(
        ...     title="Transformation Roadmap",
        ...     subtitle="Short-, medium-, and long-term priorities.",
        ...     icon="🗺️",
        ...     compact=True,
        ... )
    """

    # Alignment validation
    if align not in _VALID_ALIGNMENTS:
        raise ValueError(
            f"align must be one of {sorted(_VALID_ALIGNMENTS)}, "
            f"received '{align}'."
        )

    # Escape inputs
    escaped_title = escape(str(title))
    escaped_subtitle = (
        escape(str(subtitle))
        if subtitle is not None
        else None
    )
    escaped_eyebrow = (
        escape(str(eyebrow))
        if eyebrow is not None
        else None
    )
    escaped_icon = (
        escape(str(icon))
        if icon is not None
        else None
    )

    mapped_status = _map_status(status)

    escaped_status = (
        escape(str(mapped_status))
        if mapped_status is not None
        else None
    )

    # Build container classes
    container_classes = _build_container_classes(
        align=align,
        compact=compact,
    )

    # Build HTML
    html_parts: list[str] = [
        f'<div class="{container_classes}">'
    ]

    # Eyebrow (if provided)
    if escaped_eyebrow:
        html_parts.append(
            f'<div class="dmat-header__eyebrow">'
            f'{escaped_eyebrow}'
            f'</div>'
        )

    # Icon (if provided) + Title
    title_html = ""

    if escaped_icon:
        title_html += (
            f'<span class="dmat-header__icon">'
            f'{escaped_icon}'
            f'</span> '
        )

    title_html += (
        f'<h1 class="dmat-header__title">'
        f'{escaped_title}'
        f'</h1>'
    )

    html_parts.append(
        f'<div class="dmat-header__title-wrapper">'
        f'{title_html}'
        f'</div>'
    )

    # Subtitle (if provided)
    if escaped_subtitle:
        html_parts.append(
            f'<p class="dmat-header__subtitle">'
            f'{escaped_subtitle}'
            f'</p>'
        )

    # Status (if provided)
    if escaped_status:
        html_parts.append(
            f'<div class="dmat-header__status">'
            f'<span class="dmat-status '
            f'dmat-status--{escaped_status}">'
            f'{escaped_status.capitalize()}'
            f'</span>'
            f'</div>'
        )

    html_parts.append("</div>")

    # Render
    _render_html("\n".join(html_parts))


# ============================================================================
# PUBLIC EXPORT
# ============================================================================

__all__ = ["render_header"]