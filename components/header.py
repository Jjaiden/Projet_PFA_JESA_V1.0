# JESA_DMAT/components/header.py

"""
Composant d'en-tête de page réutilisable pour JESA DMAT.

Ce module fournit une fonction pour afficher un en-tête professionnel
dans les pages Streamlit, en utilisant le design system existant.

Utilisation typique:

    from components.header import render_header

    render_header(
        title="Digital Maturity Assessment",
        subtitle="Évaluation de la maturité digitale de votre site industriel",
        eyebrow="ASSESSMENT",
        icon="📊",
    )

Le composant utilise les classes CSS existantes du projet.
Pour un contrôle plus fin, vous pouvez étendre le CSS avec les classes
documentées ci-dessous.
"""

from __future__ import annotations

from html import escape
from typing import Any, Optional

import streamlit as st


# ============================================================================
# CONSTANTES
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
# HELPERS INTERNES
# ============================================================================

def _render_html(html: str) -> None:
    """Rend du HTML de confiance via Streamlit."""
    st.markdown(html, unsafe_allow_html=True)


def _map_status(status: Optional[str]) -> Optional[str]:
    """
    Convertit un statut sémantique en classe CSS de statut.

    Args:
        status: Statut sémantique, p. ex. "success", "advanced", "high".

    Returns:
        La classe CSS correspondante ou None.
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
    Construit la chaîne de classes CSS pour le conteneur de l'en-tête.

    Args:
        align: Alignement du contenu ("left", "center", "right").
        compact: Si True, applique un style compact.

    Returns:
        Chaîne de classes CSS.
    """
    classes = ["dmat-header"]

    # Classes d'alignement (définies dans utilities.css)
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
# FONCTION PRINCIPALE
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
    Affiche un en-tête de page professionnel.

    Args:
        title (str): Titre principal obligatoire.
        subtitle (str, optionnel): Sous-titre affiché sous le titre.
        eyebrow (str, optionnel): Texte court au-dessus du titre (ex. "ASSESSMENT").
        icon (str, optionnel): Icône (emoji ou HTML) affichée à côté du titre.
        status (str, optionnel): Statut sémantique. Valeurs possibles :
            "success", "warning", "danger", "neutral",
            "advanced", "high", "medium", "low".
            Sera mappé vers une classe CSS de statut.
        align (str): Alignement du contenu. "left", "center" ou "right".
            Par défaut "left".
        compact (bool): Si True, réduit l'espacement vertical.
        **kwargs: Arguments supplémentaires ignorés (pour extensibilité future).

    Returns:
        None

    Raises:
        ValueError: Si l'alignement n'est pas dans ["left", "center", "right"].

    Exemples:
        >>> render_header(title="Digital Maturity Assessment")

        >>> render_header(
        ...     title="Diagnostic de maturité",
        ...     subtitle="Évaluez le niveau actuel de maturité digitale.",
        ...     eyebrow="ASSESSMENT",
        ...     icon="📊",
        ... )

        >>> render_header(
        ...     title="Analyse décisionnelle",
        ...     subtitle="Identifiez les priorités de transformation.",
        ...     eyebrow="DECISION ANALYSIS",
        ...     icon="🎯",
        ...     status="warning",
        ... )

        >>> render_header(
        ...     title="Feuille de route",
        ...     subtitle="Priorités à court, moyen et long terme.",
        ...     icon="🗺️",
        ...     compact=True,
        ... )
    """

    # Validation de l'alignement
    if align not in _VALID_ALIGNMENTS:
        raise ValueError(
            f"align doit être l'un de {sorted(_VALID_ALIGNMENTS)}, "
            f"reçu '{align}'."
        )

    # Échappement des entrées
    escaped_title = escape(str(title))
    escaped_subtitle = escape(str(subtitle)) if subtitle is not None else None
    escaped_eyebrow = escape(str(eyebrow)) if eyebrow is not None else None
    escaped_icon = escape(str(icon)) if icon is not None else None
    mapped_status = _map_status(status)
    escaped_status = escape(str(mapped_status)) if mapped_status is not None else None

    # Construction des classes du conteneur
    container_classes = _build_container_classes(align=align, compact=compact)

    # Construction du HTML
    html_parts: list[str] = [
        f'<div class="{container_classes}">'
    ]

    # Eyebrow (si présent)
    if escaped_eyebrow:
        html_parts.append(
            f'<div class="dmat-header__eyebrow">{escaped_eyebrow}</div>'
        )

    # Icon (si présent) + Titre
    title_html = ""
    if escaped_icon:
        title_html += f'<span class="dmat-header__icon">{escaped_icon}</span> '
    title_html += f'<h1 class="dmat-header__title">{escaped_title}</h1>'

    html_parts.append(
        f'<div class="dmat-header__title-wrapper">{title_html}</div>'
    )

    # Subtitle (si présent)
    if escaped_subtitle:
        html_parts.append(
            f'<p class="dmat-header__subtitle">{escaped_subtitle}</p>'
        )

    # Status (si présent)
    if escaped_status:
        html_parts.append(
            f'<div class="dmat-header__status">'
            f'<span class="dmat-status dmat-status--{escaped_status}">'
            f'{escaped_status.capitalize()}'
            f'</span>'
            f'</div>'
        )

    html_parts.append("</div>")

    # Rendu
    _render_html("\n".join(html_parts))


# ============================================================================
# EXPORT PUBLIC
# ============================================================================

__all__ = ["render_header"]
