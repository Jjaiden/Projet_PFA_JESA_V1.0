"""
engines.report
--------------
Moteurs de préparation des données pour les exports et les tableaux de bord.

Ce package contient deux sous-modules :
- pdf_builder : Préparation des données et logique de mise en page pour les rapports PDF
- dashboard    : Préparation des données pour les tableaux de bord et graphiques

Exemples d'utilisation :
    from engines.report import pdf_builder, dashboard
"""

from __future__ import annotations

# ============================================================================
# Import des sous-packages (dossiers)
# ============================================================================

# On importe les modules depuis les sous-dossiers pour les exposer directement
# Les fichiers .py dans ces dossiers doivent être importés explicitement ici.

# --- Sous-package pdf_builder ---
# Exemple : from engines.report.pdf_builder.data_builder import PDFDataBuilder
#           from engines.report.pdf_builder.layout import PDFLayoutConfig
#           from engines.report.pdf_builder.elements import PDFElementFactory

# --- Sous-package dashboard ---
# Exemple : from engines.report.dashboard.metrics import DashboardMetrics
#           from engines.report.dashboard.charts import ChartDataBuilder
#           from engines.report.dashboard.filters import DataFilter


# ============================================================================
# Exports publics
# ============================================================================

__all__ = [
    # Sous-packages (pour permettre l'import via `from engines.report import pdf_builder`)
    "pdf_builder",
    "dashboard",
]