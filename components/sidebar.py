# JESA_DMAT/components/sidebar.py
"""
Composant de barre latérale (sidebar) réutilisable pour JESA DMAT.

Ce module fournit un composant pour construire le sidebar professionnel
de l'application, avec branding, navigation, informations contextuelles
et footer.

Utilisation typique:
    from components.sidebar import render_sidebar

    render_sidebar(
        title="JESA DMAT",
        subtitle="Digital Maturity Assessment Tool",
        navigation=[
            {"label": "Home", "page": "app.py", "icon": "🏠"},
            {"label": "New Assessment", "page": "pages/2_New_Assessment.py", "icon": "📝"},
        ],
        assessment_name="Site industriel A",
        assessment_status="In progress",
        show_footer=True,
    )
"""

from __future__ import annotations

from html import escape
from typing import Any, Optional, Sequence

import streamlit as st


# ============================================================================
# CONSTANTES
# ============================================================================

_DEFAULT_TITLE = "JESA DMAT"
_DEFAULT_SUBTITLE = "Digital Maturity Assessment Tool"
_DEFAULT_VERSION = "v1.0.0"


# ============================================================================
# HELPERS INTERNES
# ============================================================================

def _render_html(html: str) -> None:
    """Rend du HTML de confiance via Streamlit."""
    st.sidebar.markdown(html, unsafe_allow_html=True)


def _render_branding(
    title: str,
    subtitle: Optional[str] = None,
    logo: Optional[str] = None,
) -> None:
    """
    Affiche la section branding du sidebar.

    Args:
        title: Titre principal.
        subtitle: Sous-titre optionnel.
        logo: URL de l'image du logo ou None.
    """
    escaped_title = escape(str(title))
    escaped_subtitle = escape(str(subtitle)) if subtitle else None

    # Affichage du logo (si fourni)
    if logo:
        # use_container_width est encore valide, mais width="stretch" est recommandé pour Streamlit >=1.37
        try:
            st.sidebar.image(logo, use_container_width=True)
        except TypeError:
            # Fallback pour les versions plus récentes
            st.sidebar.image(logo, width="stretch")

    # Titre et sous-titre
    html_parts = [
        f'<div class="dmat-sidebar__brand">',
        f'<h2 class="dmat-sidebar__title">{escaped_title}</h2>',
    ]
    if escaped_subtitle:
        html_parts.append(
            f'<p class="dmat-sidebar__subtitle">{escaped_subtitle}</p>'
        )
    html_parts.append("</div>")

    _render_html("\n".join(html_parts))


def _render_navigation(
    items: Sequence[dict[str, Any]],
) -> None:
    """
    Affiche les liens de navigation dans le sidebar.

    Args:
        items: Liste de dictionnaires contenant les clés 'label', 'page',
            et optionnellement 'icon'.
    """
    if not items:
        return

    for item in items:
        label = str(item.get("label", "")).strip()
        page = item.get("page")
        icon = item.get("icon")  # peut être un emoji ou du texte, pas besoin d'échappement

        if not page:
            continue

        st.sidebar.page_link(
            page=page,
            label=label,
            icon=icon,
        )


def _render_assessment_info(
    name: Optional[str] = None,
    status: Optional[str] = None,
) -> None:
    """
    Affiche les informations contextuelles de l'évaluation en cours.

    Args:
        name: Nom du site ou de l'évaluation.
        status: Statut textuel (ex: "In progress", "Completed").
    """
    if not name and not status:
        return

    escaped_name = escape(str(name)) if name else None
    escaped_status = escape(str(status)) if status else None

    html_parts = ['<div class="dmat-sidebar__assessment">']

    if escaped_name:
        html_parts.append(
            f'<div class="dmat-sidebar__assessment-name">{escaped_name}</div>'
        )

    if escaped_status:
        html_parts.append(
            f'<div class="dmat-sidebar__assessment-status">{escaped_status}</div>'
        )

    html_parts.append('</div>')
    _render_html("\n".join(html_parts))


def _render_footer(version: Optional[str] = None) -> None:
    """
    Affiche le pied de page du sidebar.

    Args:
        version: Version de l'application.
    """
    escaped_version = escape(str(version)) if version else None

    html_parts = [
        f'<div class="dmat-sidebar__footer">',
        f'<span class="dmat-sidebar__footer-text">JESA DMAT</span>',
    ]
    if escaped_version:
        html_parts.append(
            f'<span class="dmat-sidebar__footer-version">{escaped_version}</span>'
        )
    html_parts.append('</div>')

    _render_html("\n".join(html_parts))


# ============================================================================
# COMPOSANT PUBLIC
# ============================================================================

def render_sidebar(
    title: str = _DEFAULT_TITLE,
    subtitle: Optional[str] = _DEFAULT_SUBTITLE,
    logo: Optional[str] = None,
    navigation: Optional[Sequence[dict[str, Any]]] = None,
    assessment_name: Optional[str] = None,
    assessment_status: Optional[str] = None,
    show_footer: bool = True,
    version: Optional[str] = _DEFAULT_VERSION,
    **kwargs: Any,
) -> None:
    """
    Affiche le sidebar professionnel de JESA DMAT.

    Args:
        title (str): Titre principal du produit. Par défaut "JESA DMAT".
        subtitle (str, optionnel): Sous-titre. Par défaut "Digital Maturity Assessment Tool".
        logo (str, optionnel): URL de l'image du logo (peut être un chemin local).
        navigation (Sequence[dict], optionnel): Liste des éléments de navigation.
            Chaque élément doit avoir les clés 'label' et 'page' (chemin vers la page),
            et peut avoir une clé 'icon' (emoji ou texte).
            Exemple: [{"label": "Home", "page": "app.py", "icon": "🏠"}]
        assessment_name (str, optionnel): Nom de l'évaluation ou du site industriel.
        assessment_status (str, optionnel): Statut textuel de l'évaluation.
        show_footer (bool): Si True, affiche le pied de page avec la version.
        version (str, optionnel): Version de l'application à afficher dans le footer.
        **kwargs: Arguments supplémentaires ignorés (extensibilité).

    Returns:
        None

    Exemple:
        render_sidebar(
            title="JESA DMAT",
            subtitle="Digital Maturity Assessment Tool",
            navigation=[
                {"label": "Home", "page": "app.py", "icon": "🏠"},
                {"label": "New Assessment", "page": "pages/2_New_Assessment.py", "icon": "📝"},
            ],
            assessment_name="Site industriel A",
            assessment_status="In progress",
            show_footer=True,
        )
    """

    # Branding
    _render_branding(title, subtitle, logo)

    # Séparateur
    st.sidebar.divider()

    # Navigation
    if navigation:
        _render_navigation(navigation)
        st.sidebar.divider()

    # Informations sur l'évaluation
    if assessment_name or assessment_status:
        _render_assessment_info(assessment_name, assessment_status)
        st.sidebar.divider()

    # Footer
    if show_footer:
        _render_footer(version)


# ============================================================================
# EXPORT PUBLIC
# ============================================================================

__all__ = ["render_sidebar"]