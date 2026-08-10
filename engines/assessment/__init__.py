"""
engines.assessment
------------------
Moteurs d'évaluation de la maturité digitale.

Ce package contient :
- aggregation.py  : Orchestration du calcul hiérarchique (Indicateur → SD → D → Pilier → DMI)
- scoring.py      : Calcul des scores individuels et agrégés
- maturity.py     : Interprétation des niveaux de maturité
- validator.py    : Validation du référentiel et des évaluations

Exports publics :
    AggregationEngine, ScoringEngine, MaturityEngine
    ScoreResult, MaturityResult
    validate_referentiel, validate_assessment, ensure_valid
"""

from __future__ import annotations

from engines.assessment.aggregation import AggregationEngine
from engines.assessment.scoring import ScoringEngine, ScoreResult
from engines.assessment.maturity import MaturityEngine, MaturityResult
from engines.assessment.validator import (
    validate_referentiel,
    validate_assessment,
    ensure_valid,
    ValidationReport,
    ValidationBlockingError,
)

__all__ = [
    # Agrégation
    "AggregationEngine",
    # Scoring
    "ScoringEngine",
    "ScoreResult",
    # Maturité
    "MaturityEngine",
    "MaturityResult",
    # Validation
    "validate_referentiel",
    "validate_assessment",
    "ensure_valid",
    "ValidationReport",
    "ValidationBlockingError",
]