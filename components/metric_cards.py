# JESA_DMAT/components/metric_cards.py
"""
Composants de métriques spécialisés pour le Dashboard DMAT.

Ce module fournit des composants UI pour afficher les indicateurs clés
de maturité digitale, tels que le score global, les scores par pilier,
et les tendances d'évolution.

Ces composants sont destinés au Dashboard et aux pages d'analyse,
et utilisent le design system JESA DMAT.

Ils se distinguent des cartes génériques de `cards.py` par leur
spécialisation pour des métriques de maturité (score, niveau, tendance).

Utilisation typique:
    from components.metric_cards import (
        render_maturity_metric,
        render_pillar_metric,
        render_trend_metric,
    )

    render_maturity_metric(
        label="Maturité globale",
        value=72,
        unit="%",
        level="Advanced",
        icon="📊",
        precision=1,  # affiche une décimale
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
# CONSTANTES
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
# HELPERS INTERNES
# ============================================================================

def _render_html(html: str) -> None:
    """Rend du HTML de confiance via Streamlit."""
    st.markdown(html, unsafe_allow_html=True)


def _map_status_to_metric(status: Optional[str]) -> Optional[str]:
    """
    Convertit un statut sémantique en classe CSS de métrique.

    Args:
        status: Statut sémantique, p. ex. "success", "advanced", "high".

    Returns:
        La classe CSS correspondante ("positive", "warning", "negative",
        "neutral") ou None.
    """
    if status is None:
        return None

    normalized = str(status).strip().lower()
    return _STATUS_MAP.get(normalized, normalized)


def _format_number(value: Any, decimals: Optional[int] = None) -> str:
    """
    Formate une valeur numérique pour affichage.

    Args:
        value: Valeur à formater (int, float ou autre).
        decimals: Nombre de décimales à afficher. Si None, utilise le
            format `:g` qui supprime les zéros inutiles.

    Returns:
        Chaîne formatée.
    """
    if isinstance(value, (int, float)):
        if decimals is not None:
            return f"{value:.{decimals}f}"
        return f"{value:g}"
    return str(value)


def _build_metric_classes(status: Optional[str] = None) -> str:
    """
    Construit la chaîne de classes CSS pour une métrique.

    Args:
        status: Statut sémantique (sera mappé vers une classe de métrique).

    Returns:
        Chaîne de classes CSS.
    """
    classes = ["dmat-metric"]

    mapped = _map_status_to_metric(status)
    if mapped:
        classes.append(f"dmat-metric--{mapped}")

    return " ".join(classes)


# ============================================================================
# COMPOSANTS PUBLICS
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
    Affiche une métrique de maturité globale avec niveau textuel.

    Args:
        label (str): Libellé de la métrique.
        value (float | int): Valeur numérique du score.
        unit (str, optionnel): Unité (ex: "%"). Un espace sera ajouté.
        level (str, optionnel): Niveau de maturité textuel (ex: "Advanced").
        icon (str, optionnel): Icône (emoji ou HTML) à afficher.
        status (str, optionnel): Statut sémantique. Sera mappé vers une
            classe de style de métrique.
        precision (int, optionnel): Nombre de décimales à afficher.
        **kwargs: Arguments supplémentaires ignorés (extensibilité).

    Returns:
        None

    Exemple:
        render_maturity_metric(
            label="Maturité globale",
            value=72.4,
            unit="%",
            level="Advanced",
            status="success",
            icon="📊",
            precision=1,
        )
    """
    # Échappement des entrées
    escaped_label = escape(str(label))
    escaped_value = escape(_format_number(value, precision))
    escaped_level = escape(str(level)) if level is not None else None
    escaped_icon = escape(str(icon)) if icon is not None else None

    # Ajout de l'unité
    if unit:
        escaped_value += f" {unit}"

    classes = _build_metric_classes(status)

    html_parts = [
        f'<div class="{classes}">'
    ]

    # Icône (si présente)
    if escaped_icon:
        html_parts.append(
            f'<div class="dmat-metric__icon">{escaped_icon}</div>'
        )

    # Label
    html_parts.append(
        f'<div class="dmat-metric__label">{escaped_label}</div>'
    )

    # Valeur
    html_parts.append(
        f'<div class="dmat-metric__value">{escaped_value}</div>'
    )

    # Niveau (si présent)
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
    Affiche une métrique pour un pilier de maturité.

    Args:
        label (str): Libellé du pilier.
        value (float | int): Valeur du score.
        unit (str, optionnel): Unité (ex: "%").
        icon (str, optionnel): Icône (emoji ou HTML) à afficher.
        status (str, optionnel): Statut sémantique. Sera mappé vers une
            classe de style de métrique.
        precision (int, optionnel): Nombre de décimales à afficher.
        **kwargs: Arguments supplémentaires ignorés (extensibilité).

    Returns:
        None

    Exemple:
        render_pillar_metric(
            label="Infrastructure",
            value=85,
            unit="%",
            status="success",
            icon="🏭",
        )
    """
    # Échappement des entrées
    escaped_label = escape(str(label))
    escaped_value = escape(_format_number(value, precision))
    escaped_icon = escape(str(icon)) if icon is not None else None

    # Ajout de l'unité
    if unit:
        escaped_value += f" {unit}"

    classes = _build_metric_classes(status)

    html_parts = [
        f'<div class="{classes}">'
    ]

    # Icône (si présente)
    if escaped_icon:
        html_parts.append(
            f'<div class="dmat-metric__icon">{escaped_icon}</div>'
        )

    # Label
    html_parts.append(
        f'<div class="dmat-metric__label">{escaped_label}</div>'
    )

    # Valeur
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
    Affiche une métrique avec tendance (delta) et statut de tendance.

    Args:
        label (str): Libellé de la métrique.
        value (float | int): Valeur actuelle.
        unit (str, optionnel): Unité (ex: "%").
        delta (str, optionnel): Texte de variation (ex: "+5%", "-2").
        trend (str, optionnel): Tendance sémantique ("positive", "negative",
            "neutral", "success", "warning", etc.). Sera mappé vers une
            classe de style de métrique.
        icon (str, optionnel): Icône (emoji ou HTML) à afficher.
        precision (int, optionnel): Nombre de décimales à afficher.
        **kwargs: Arguments supplémentaires ignorés (extensibilité).

    Returns:
        None

    Exemple:
        render_trend_metric(
            label="Progression",
            value=72,
            unit="%",
            delta="+5%",
            trend="positive",
            icon="📈",
            precision=1,
        )
    """
    # Échappement des entrées
    escaped_label = escape(str(label))
    escaped_value = escape(_format_number(value, precision))
    escaped_delta = escape(str(delta)) if delta is not None else None
    escaped_icon = escape(str(icon)) if icon is not None else None

    # Ajout de l'unité
    if unit:
        escaped_value += f" {unit}"

    classes = _build_metric_classes(trend)

    html_parts = [
        f'<div class="{classes}">'
    ]

    # Icône (si présente)
    if escaped_icon:
        html_parts.append(
            f'<div class="dmat-metric__icon">{escaped_icon}</div>'
        )

    # Label
    html_parts.append(
        f'<div class="dmat-metric__label">{escaped_label}</div>'
    )

    # Valeur
    html_parts.append(
        f'<div class="dmat-metric__value">{escaped_value}</div>'
    )

    # Delta (si présent)
    if escaped_delta:
        html_parts.append(
            f'<div class="dmat-metric__delta">{escaped_delta}</div>'
        )

    html_parts.append("</div>")

    _render_html("\n".join(html_parts))


# ============================================================================
# COMPOSANTS PUBLICS
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
    Affiche une métrique de maturité globale avec niveau textuel.

    Args:
        label (str): Libellé de la métrique.
        value (float | int): Valeur numérique du score.
        unit (str, optionnel): Unité (ex: "%"). Un espace sera ajouté.
        level (str, optionnel): Niveau de maturité textuel (ex: "Advanced").
        icon (str, optionnel): Icône (emoji ou HTML) à afficher.
        status (str, optionnel): Statut sémantique. Sera mappé vers une
            classe de style de métrique.
        precision (int, optionnel): Nombre de décimales à afficher.
        **kwargs: Arguments supplémentaires ignorés (extensibilité).

    Returns:
        None

    Exemple:
        render_maturity_metric(
            label="Maturité globale",
            value=72.4,
            unit="%",
            level="Advanced",
            status="success",
            icon="📊",
            precision=1,
        )
    """
    # Échappement des entrées
    escaped_label = escape(str(label))
    escaped_value = escape(_format_number(value, precision))
    escaped_level = escape(str(level)) if level is not None else None
    escaped_icon = escape(str(icon)) if icon is not None else None

    # Ajout de l'unité
    if unit:
        escaped_value += f" {unit}"

    classes = _build_metric_classes(status)

    html_parts = [
        f'<div class="{classes}">'
    ]

    # Icône (si présente)
    if escaped_icon:
        html_parts.append(
            f'<div class="dmat-metric__icon">{escaped_icon}</div>'
        )

    # Label
    html_parts.append(
        f'<div class="dmat-metric__label">{escaped_label}</div>'
    )

    # Valeur
    html_parts.append(
        f'<div class="dmat-metric__value">{escaped_value}</div>'
    )

    # Niveau (si présent)
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
    Affiche une métrique pour un pilier de maturité.

    Args:
        label (str): Libellé du pilier.
        value (float | int): Valeur du score.
        unit (str, optionnel): Unité (ex: "%").
        icon (str, optionnel): Icône (emoji ou HTML) à afficher.
        status (str, optionnel): Statut sémantique. Sera mappé vers une
            classe de style de métrique.
        precision (int, optionnel): Nombre de décimales à afficher.
        **kwargs: Arguments supplémentaires ignorés (extensibilité).

    Returns:
        None

    Exemple:
        render_pillar_metric(
            label="Infrastructure",
            value=85,
            unit="%",
            status="success",
            icon="🏭",
        )
    """
    # Échappement des entrées
    escaped_label = escape(str(label))
    escaped_value = escape(_format_number(value, precision))
    escaped_icon = escape(str(icon)) if icon is not None else None

    # Ajout de l'unité
    if unit:
        escaped_value += f" {unit}"

    classes = _build_metric_classes(status)

    html_parts = [
        f'<div class="{classes}">'
    ]

    # Icône (si présente)
    if escaped_icon:
        html_parts.append(
            f'<div class="dmat-metric__icon">{escaped_icon}</div>'
        )

    # Label
    html_parts.append(
        f'<div class="dmat-metric__label">{escaped_label}</div>'
    )

    # Valeur
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
    Affiche une métrique avec tendance (delta) et statut de tendance.

    Args:
        label (str): Libellé de la métrique.
        value (float | int): Valeur actuelle.
        unit (str, optionnel): Unité (ex: "%").
        delta (str, optionnel): Texte de variation (ex: "+5%", "-2").
        trend (str, optionnel): Tendance sémantique ("positive", "negative",
            "neutral", "success", "warning", etc.). Sera mappé vers une
            classe de style de métrique.
        icon (str, optionnel): Icône (emoji ou HTML) à afficher.
        precision (int, optionnel): Nombre de décimales à afficher.
        **kwargs: Arguments supplémentaires ignorés (extensibilité).

    Returns:
        None

    Exemple:
        render_trend_metric(
            label="Progression",
            value=72,
            unit="%",
            delta="+5%",
            trend="positive",
            icon="📈",
            precision=1,
        )
    """
    # Échappement des entrées
    escaped_label = escape(str(label))
    escaped_value = escape(_format_number(value, precision))
    escaped_delta = escape(str(delta)) if delta is not None else None
    escaped_icon = escape(str(icon)) if icon is not None else None

    # Ajout de l'unité
    if unit:
        escaped_value += f" {unit}"

    classes = _build_metric_classes(trend)

    html_parts = [
        f'<div class="{classes}">'
    ]

    # Icône (si présente)
    if escaped_icon:
        html_parts.append(
            f'<div class="dmat-metric__icon">{escaped_icon}</div>'
        )

    # Label
    html_parts.append(
        f'<div class="dmat-metric__label">{escaped_label}</div>'
    )

    # Valeur
    html_parts.append(
        f'<div class="dmat-metric__value">{escaped_value}</div>'
    )

    # Delta (si présent)
    if escaped_delta:
        html_parts.append(
            f'<div class="dmat-metric__delta">{escaped_delta}</div>'
        )

    html_parts.append("</div>")

    _render_html("\n".join(html_parts))


# ============================================================================
# EXPORT PUBLIC
# ============================================================================

__all__ = [
    "render_maturity_metric",
    "render_pillar_metric",
    "render_trend_metric",
]