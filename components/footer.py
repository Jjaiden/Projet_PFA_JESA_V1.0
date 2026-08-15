# JESA_DMAT/components/footer.py

"""
Reusable footer component for JESA DMAT.

This module provides a component for displaying a professional footer
in Streamlit pages, using the existing design system.

Typical usage:
from components.footer import render_footer

# Simple footer
render_footer()

# Full footer
render_footer(
    product_name="JESA DMAT",
    version="v1.0.0",
    organization="JESA",
    copyright_text="© 2026 JESA. All rights reserved.",
    tagline="Digital Maturity Assessment Tool",
    links=[
        {"label": "JESA", "url": "https://www.jesa.ma"},
        {"label": "Support", "url": "#"},
    ],
    align="center",
    compact=False,
    show_divider=True,
)
"""

from __future__ import annotations

import datetime
from html import escape
from typing import Any, Optional, Sequence

import streamlit as st


# ============================================================================
# CONSTANTS
# ============================================================================

_VALID_ALIGNMENTS = {"left", "center", "right"}


# ============================================================================
# INTERNAL HELPERS
# ============================================================================


def _render_html(html: str) -> None:
    """
    Render HTML through Streamlit.

    Uses st.markdown with unsafe_allow_html=True to remain consistent
    with the other project components.
    """
    st.markdown(html, unsafe_allow_html=True)


def _build_footer_classes(
    align: str = "center",
    compact: bool = False,
) -> str:
    """
    Build the CSS class string for the footer container.

    Args:
        align: Content alignment ("left", "center", "right").
        compact: If True, applies compact styling.

    Returns:
        CSS class string.
    """
    classes = ["dmat-footer"]

    # Alignment classes defined in utilities.css
    if align == "left":
        classes.append("u-text-left")
    elif align == "center":
        classes.append("u-text-center")
    elif align == "right":
        classes.append("u-text-right")

    if compact:
        classes.append("dmat-footer--compact")

    return " ".join(classes)


def _build_copyright(
    organization: str,
    copyright_text: Optional[str] = None,
) -> str:
    """
    Generate the copyright text.

    Args:
        organization: Organization name.
        copyright_text: Custom copyright text.

    Returns:
        Escaped copyright text.
    """
    if copyright_text:
        return escape(copyright_text)

    current_year = datetime.date.today().year
    safe_organization = escape(str(organization))

    return f"© {current_year} {safe_organization}"


def _render_link(
    link: dict[str, str],
) -> Optional[str]:
    """
    Render an HTML link from a dictionary.

    Args:
        link: Dictionary containing 'label' and 'url'.

    Returns:
        HTML link string, or None if invalid.
    """
    label = link.get("label", "").strip()
    url = link.get("url", "").strip()

    if not label or not url:
        return None

    escaped_label = escape(label)
    escaped_url = escape(url)

    return (
        f'<a class="dmat-footer__link" '
        f'href="{escaped_url}" '
        f'target="_blank" '
        f'rel="noopener noreferrer">'
        f"{escaped_label}"
        f"</a>"
    )


# ============================================================================
# PUBLIC FUNCTION
# ============================================================================


def render_footer(
    product_name: str = "JESA DMAT",
    version: Optional[str] = "v1.0.0",
    copyright_text: Optional[str] = None,
    organization: str = "JESA",
    tagline: Optional[str] = None,
    links: Optional[Sequence[dict[str, str]]] = None,
    show_divider: bool = True,
    align: str = "center",
    compact: bool = False,
    **kwargs: Any,
) -> None:
    """
    Display a professional footer.

    Args:
        product_name (str): Product name. Defaults to "JESA DMAT".
        version (str, optional): Product version. Defaults to "v1.0.0".
        copyright_text (str, optional): Custom copyright text.
            If not provided, it is automatically generated from
            `organization` and the current year.
        organization (str): Organization name. Defaults to "JESA".
        tagline (str, optional): Tagline or short description.
        links (Sequence[dict], optional): List of dictionaries containing
            the keys 'label' and 'url'. Example:
            [{"label": "JESA", "url": "https://www.jesa.ma"}]
        show_divider (bool): If True, displays a divider above the footer.
        align (str): Content alignment. "left", "center", or "right".
            Defaults to "center".
        compact (bool): If True, reduces vertical spacing.
        **kwargs: Additional ignored arguments for extensibility.

    Returns:
        None

    Raises:
        ValueError: If alignment is not one of
            ["left", "center", "right"].

    Examples:
        >>> render_footer()

        >>> render_footer(
        ...     product_name="JESA DMAT",
        ...     version="v1.0.0",
        ...     organization="JESA",
        ...     copyright_text="© 2026 JESA. All rights reserved.",
        ...     tagline="Digital Maturity Assessment Tool",
        ...     links=[
        ...         {"label": "JESA", "url": "https://www.jesa.ma"},
        ...         {"label": "Support", "url": "#"},
        ...     ],
        ... )
    """

    # Alignment validation
    if align not in _VALID_ALIGNMENTS:
        raise ValueError(
            f"align must be one of {sorted(_VALID_ALIGNMENTS)}, "
            f"received '{align}'."
        )

    # Divider — completely removed to avoid double lines
    if show_divider:
        # Add some vertical space instead of a divider
        st.markdown(
            '<div style="height: 0.5rem;"></div>',
            unsafe_allow_html=True,
        )

    # Build container classes
    container_classes = _build_footer_classes(
        align=align,
        compact=compact,
    )

    # Escape inputs
    escaped_product = escape(str(product_name))
    escaped_version = (
        escape(str(version))
        if version is not None
        else None
    )
    escaped_tagline = (
        escape(str(tagline))
        if tagline
        else None
    )

    copyright_html = _build_copyright(
        organization,
        copyright_text,
    )

    # Build HTML
    html_parts = [
        f'<div class="{container_classes}">',
        '<div class="dmat-footer__content">',
    ]

    # Branding (product + version)
    brand_parts = [
        f'<span class="dmat-footer__product">'
        f"{escaped_product}"
        f"</span>"
    ]

    if escaped_version:
        brand_parts.append(
            f'<span class="dmat-footer__version">'
            f"{escaped_version}"
            f"</span>"
        )

    html_parts.append(
        f'<div class="dmat-footer__brand">'
        f'{" ".join(brand_parts)}'
        f"</div>"
    )

    # Tagline
    if escaped_tagline:
        html_parts.append(
            f'<div class="dmat-footer__tagline">'
            f"{escaped_tagline}"
            f"</div>"
        )

    # Copyright / Organization
    html_parts.append(
        f'<div class="dmat-footer__copyright">'
        f"{copyright_html}"
        f"</div>"
    )

    # Links
    if links:
        link_htmls = []

        for link in links:
            link_html = _render_link(link)

            if link_html:
                link_htmls.append(link_html)

        if link_htmls:
            html_parts.append(
                f'<div class="dmat-footer__links">'
                f'{" • ".join(link_htmls)}'
                f"</div>"
            )

    html_parts.append("</div>")  # End content
    html_parts.append("</div>")  # End footer

    # Render
    _render_html("\n".join(html_parts))


# ============================================================================
# PUBLIC EXPORT
# ============================================================================

__all__ = ["render_footer"]