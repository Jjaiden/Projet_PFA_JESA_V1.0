"""
data
----
Chargement et modèles de données du JDMAF.

Ce package contient :
- loader.py : Chargement des fichiers Excel (Référentiel et Assessment)
- models.py : Structures de données (dataclasses) pour le référentiel et l'évaluation

Exports publics :
    load_referentiel(path=None) -> Referentiel
    load_assessment(path=None) -> Assessment
    Referentiel, Assessment, Pillar, Dimension, Subdimension, Indicator, ...
"""

from __future__ import annotations

from data.loader import load_referentiel, load_assessment
from data.models import (
    # Référentiel
    Referentiel,
    Pillar,
    Dimension,
    Subdimension,
    Indicator,
    MaturityLevelDescription,
    DimensionMaturityLevel,
    IndicatorScoringGridEntry,
    EvidenceCatalogEntry,
    WeightEntry,
    # Assessment
    Assessment,
    AssessmentMetadata,
    IndicatorScore,
)

__all__ = [
    # Chargement
    "load_referentiel",
    "load_assessment",
    # Modèles
    "Referentiel",
    "Pillar",
    "Dimension",
    "Subdimension",
    "Indicator",
    "MaturityLevelDescription",
    "DimensionMaturityLevel",
    "IndicatorScoringGridEntry",
    "EvidenceCatalogEntry",
    "WeightEntry",
    "Assessment",
    "AssessmentMetadata",
    "IndicatorScore",
]