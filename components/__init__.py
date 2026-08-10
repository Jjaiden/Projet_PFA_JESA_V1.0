# JESA_DMAT/components/__init__.py
"""
Composants UI réutilisables pour l'application JESA DMAT.

Ce package fournit des composants de présentation pour les pages Streamlit,
tels que des cartes, en-têtes, pieds de page, barres latérales, métriques
et tableaux. Tous les composants sont frontend-only et ne contiennent
aucune logique métier.

Exports publics :
    - render_card, render_metric_card (cards)
    - render_header (header)
    - render_sidebar (sidebar)
    - render_footer (footer)
    - render_maturity_metric, render_pillar_metric, render_trend_metric (metric_cards)
    - render_data_table, render_status_table, render_score_table (tables)
"""

from __future__ import annotations

from .cards import render_card, render_metric_card
from .footer import render_footer
from .header import render_header
from .metric_cards import (
    render_maturity_metric,
    render_pillar_metric,
    render_trend_metric,
)
from .sidebar import render_sidebar
from .tables import (
    render_data_table,
    render_status_table,
    render_score_table,
)

__all__ = [
    "render_card",
    "render_metric_card",
    "render_header",
    "render_sidebar",
    "render_footer",
    "render_maturity_metric",
    "render_pillar_metric",
    "render_trend_metric",
    "render_data_table",
    "render_status_table",
    "render_score_table",
]