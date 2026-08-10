# JESA_DMAT/components/footer.py
"""
Composant de pied de page réutilisable pour JESA DMAT.

Ce module fournit un composant pour afficher un footer professionnel
dans les pages Streamlit, en utilisant le design system existant.

Utilisation typique:
    from components.footer import render_footer

    # Footer simple
    render_footer()

    # Footer complet
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
# CONSTANTES
# ============================================================================

_VALID_ALIGNMENTS = {"left", "center", "right"}


# ============================================================================
# HELPERS INTERNES
# ============================================================================

def _render_html(html: str) -> None:
    """
    Rend du HTML via Streamlit.

    Utilise st.markdown avec unsafe_allow_html=True pour rester cohérent
    avec les autres composants du projet (cards.py, header.py, etc.).
    Si la version de Streamlit est suffisamment récente (>1.36), on pourrait
    utiliser st.html() mais cela nécessiterait de changer tous les composants.
    """
    st.markdown(html, unsafe_allow_html=True)


def _build_footer_classes(align: str = "center", compact: bool = False) -> str:
    """
    Construit la chaîne de classes CSS pour le conteneur du footer.

    Args:
        align: Alignement du contenu ("left", "center", "right").
        compact: Si True, applique un style compact.

    Returns:
        Chaîne de classes CSS.
    """
    classes = ["dmat-footer"]

    # Classes d'alignement (définies dans utilities.css)
    if align == "left":
        classes.append("u-text-left")
    elif align == "center":
        classes.append("u-text-center")
    elif align == "right":
        classes.append("u-text-right")

    if compact:
        classes.append("dmat-footer--compact")

    return " ".join(classes)


def _build_copyright(organization: str, copyright_text: Optional[str] = None) -> str:
    """
    Génère le texte du copyright.

    Args:
        organization: Nom de l'organisation.
        copyright_text: Texte de copyright personnalisé.

    Returns:
        Texte du copyright échappé.
    """
    if copyright_text:
        return escape(copyright_text)

    current_year = datetime.date.today().year
    safe_organization = escape(str(organization))
    return f"© {current_year} {safe_organization}"


def _render_link(link: dict[str, str]) -> Optional[str]:
    """
    Rend un lien HTML à partir d'un dictionnaire.

    Args:
        link: Dictionnaire contenant 'label' et 'url'.

    Returns:
        Chaîne HTML du lien, ou None si invalide.
    """
    label = link.get("label", "").strip()
    url = link.get("url", "").strip()

    if not label or not url:
        return None

    escaped_label = escape(label)
    escaped_url = escape(url)

    return f'<a class="dmat-footer__link" href="{escaped_url}" target="_blank" rel="noopener noreferrer">{escaped_label}</a>'


# ============================================================================
# FONCTION PUBLIQUE
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
    Affiche un pied de page professionnel.

    Args:
        product_name (str): Nom du produit. Par défaut "JESA DMAT".
        version (str, optionnel): Version du produit. Par défaut "v1.0.0".
        copyright_text (str, optionnel): Texte de copyright personnalisé.
            Si non fourni, généré automatiquement à partir de `organization`
            et de l'année courante.
        organization (str): Nom de l'organisation. Par défaut "JESA".
        tagline (str, optionnel): Slogan ou phrase d'accroche.
        links (Sequence[dict], optionnel): Liste de dictionnaires contenant
            les clés 'label' et 'url'. Exemple:
            [{"label": "JESA", "url": "https://www.jesa.ma"}]
        show_divider (bool): Si True, affiche un séparateur au-dessus du footer.
        align (str): Alignement du contenu. "left", "center" ou "right".
            Par défaut "center".
        compact (bool): Si True, réduit l'espacement vertical.
        **kwargs: Arguments supplémentaires ignorés (extensibilité).

    Returns:
        None

    Raises:
        ValueError: Si l'alignement n'est pas dans ["left", "center", "right"].

    Exemples:
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
    # Validation de l'alignement
    if align not in _VALID_ALIGNMENTS:
        raise ValueError(
            f"align doit être l'un de {sorted(_VALID_ALIGNMENTS)}, "
            f"reçu '{align}'."
        )

    # Séparateur
    if show_divider:
        st.divider()

    # Construction des classes du conteneur
    container_classes = _build_footer_classes(align=align, compact=compact)

    # Échappement des entrées
    escaped_product = escape(str(product_name))
    escaped_version = escape(str(version)) if version is not None else None
    escaped_tagline = escape(str(tagline)) if tagline else None
    copyright_html = _build_copyright(organization, copyright_text)

    # Construction du HTML
    html_parts = [
        f'<div class="{container_classes}">',
        '<div class="dmat-footer__content">',
    ]

    # Branding (produit + version)
    brand_parts = [
        f'<span class="dmat-footer__product">{escaped_product}</span>'
    ]
    if escaped_version:
        brand_parts.append(
            f'<span class="dmat-footer__version">{escaped_version}</span>'
        )
    html_parts.append(
        f'<div class="dmat-footer__brand">{" ".join(brand_parts)}</div>'
    )

    # Tagline
    if escaped_tagline:
        html_parts.append(
            f'<div class="dmat-footer__tagline">{escaped_tagline}</div>'
        )

    # Copyright / Organization
    html_parts.append(
        f'<div class="dmat-footer__copyright">{copyright_html}</div>'
    )

    # Liens
    if links:
        link_htmls = []
        for link in links:
            link_html = _render_link(link)
            if link_html:
                link_htmls.append(link_html)
        if link_htmls:
            html_parts.append(
                f'<div class="dmat-footer__links">{" • ".join(link_htmls)}</div>'
            )

    html_parts.append("</div>")  # fin content
    html_parts.append("</div>")  # fin footer

    # Rendu
    _render_html("\n".join(html_parts))


# ============================================================================
# EXPORT PUBLIC
# ============================================================================

__all__ = ["render_footer"]