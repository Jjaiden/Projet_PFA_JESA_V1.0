"""
data
----
JDMAF data loading and models.

This package contains:
- loader.py: Excel file loading (Referential and Assessment)
- models.py: Data structures (dataclasses) for the referential and assessment

Public exports:
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