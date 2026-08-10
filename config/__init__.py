"""
config
------
Configuration et constantes du projet JDMAF.

Ce package centralise toutes les configurations et constantes
nécessaires au backend (moteurs de calcul, loader, validation)
et au frontend (Streamlit, UI, exports).

Exports principaux:
    from config import settings, constants

    - settings: Instance globale de Settings (backend + frontend)
    - constants: Toutes les constantes backend + frontend
"""

from __future__ import annotations

# ============================================================================
# Exports principaux
# ============================================================================

from config.settings import settings
from config.constants import (
    # Backend
    SCORE_MIN,
    SCORE_MAX,
    VALID_INDICATOR_SCORES,
    MATURITY_LEVELS,
    MATURITY_LEVEL_DESCRIPTIONS,
    PILLARS,
    PILLAR_IDS,
    DIMENSIONS,
    DIMENSION_IDS,
    DIMENSION_TO_PILLAR,
    PILLAR_TO_DIMENSIONS,
    SUBDIMENSIONS,
    SUBDIMENSION_IDS,
    SUBDIMENSION_TO_DIMENSION,
    DIMENSION_TO_SUBDIMENSIONS,
    INDICATORS_PER_SUBDIMENSION,
    EXPECTED_INDICATOR_COUNT,
    APPLICABILITY_APPLICABLE,
    APPLICABILITY_NOT_APPLICABLE,
    VALID_APPLICABILITY_VALUES,
    WEIGHT_SUM_TOLERANCE,
    DEFAULT_WEIGHT_PILLAR,
    DEFAULT_WEIGHT_DIMENSION_PER_PILLAR,
    DEFAULT_WEIGHT_SUBDIMENSION_PER_DIMENSION,
    DMI_SCALE_FACTOR,
    WEAKNESS_CAP_INCREMENT,
    FULL_SATISFACTION_REQUIRED,
    MATURITY_BANDS,
    MATURITY_BAND_NAMES,
    get_maturity_band,
    HierarchyLevel,
    HIERARCHY_LEVELS,
    ENTITY_TYPES,
    TPI_PARAMETERS_FAVORABLE,
    TPI_PARAMETERS_INVERTED,
    TPI_ALL_PARAMETERS,
    DEFAULT_TPI_WEIGHT,
    TPI_PRIORITY_THRESHOLDS,
    GAP_THRESHOLDS,
    RefSheets,
    REFERENTIEL_SHEETS,
    KnowledgeBaseSheets,
    KNOWLEDGE_BASE_SHEETS,
    ERROR_MESSAGES,
    EXPECTED_PILLAR_COUNT,
    EXPECTED_DIMENSION_COUNT,
    EXPECTED_SUBDIMENSION_COUNT,
    DIMENSIONS_PER_PILLAR,
    SUBDIMENSIONS_PER_DIMENSION,

    # Frontend
    APP,
    Page,
    MaturityLevel,
    Pillar,
    NUMBER_OF_PILLARS,
    Priority,
    Status,
    ALLOWED_EXTENSIONS,
    ExportFormat,
    SHEET_ASSESSMENT,
    SHEET_KNOWLEDGE_BASE,
    PAGE_ICONS,
    MAX_SCORE,
    MIN_MATURITY_LEVEL,
    MAX_MATURITY_LEVEL,
)

# ============================================================================
# Version du package
# ============================================================================

__version__ = "1.0.0"

# ============================================================================
# Liste des exports publics (pour `from config import *`)
# ============================================================================

__all__ = [
    # Instance globale
    "settings",

    # Backend
    "SCORE_MIN",
    "SCORE_MAX",
    "VALID_INDICATOR_SCORES",
    "MATURITY_LEVELS",
    "MATURITY_LEVEL_DESCRIPTIONS",
    "PILLARS",
    "PILLAR_IDS",
    "DIMENSIONS",
    "DIMENSION_IDS",
    "DIMENSION_TO_PILLAR",
    "PILLAR_TO_DIMENSIONS",
    "SUBDIMENSIONS",
    "SUBDIMENSION_IDS",
    "SUBDIMENSION_TO_DIMENSION",
    "DIMENSION_TO_SUBDIMENSIONS",
    "INDICATORS_PER_SUBDIMENSION",
    "EXPECTED_INDICATOR_COUNT",
    "APPLICABILITY_APPLICABLE",
    "APPLICABILITY_NOT_APPLICABLE",
    "VALID_APPLICABILITY_VALUES",
    "WEIGHT_SUM_TOLERANCE",
    "DEFAULT_WEIGHT_PILLAR",
    "DEFAULT_WEIGHT_DIMENSION_PER_PILLAR",
    "DEFAULT_WEIGHT_SUBDIMENSION_PER_DIMENSION",
    "DMI_SCALE_FACTOR",
    "WEAKNESS_CAP_INCREMENT",
    "FULL_SATISFACTION_REQUIRED",
    "MATURITY_BANDS",
    "MATURITY_BAND_NAMES",
    "get_maturity_band",
    "HierarchyLevel",
    "HIERARCHY_LEVELS",
    "ENTITY_TYPES",
    "TPI_PARAMETERS_FAVORABLE",
    "TPI_PARAMETERS_INVERTED",
    "TPI_ALL_PARAMETERS",
    "DEFAULT_TPI_WEIGHT",
    "TPI_PRIORITY_THRESHOLDS",
    "GAP_THRESHOLDS",
    "RefSheets",
    "REFERENTIEL_SHEETS",
    "KnowledgeBaseSheets",
    "KNOWLEDGE_BASE_SHEETS",
    "ERROR_MESSAGES",
    "EXPECTED_PILLAR_COUNT",
    "EXPECTED_DIMENSION_COUNT",
    "EXPECTED_SUBDIMENSION_COUNT",
    "DIMENSIONS_PER_PILLAR",
    "SUBDIMENSIONS_PER_DIMENSION",

    # Frontend
    "APP",
    "Page",
    "MaturityLevel",
    "Pillar",
    "NUMBER_OF_PILLARS",
    "Priority",
    "Status",
    "ALLOWED_EXTENSIONS",
    "ExportFormat",
    "SHEET_ASSESSMENT",
    "SHEET_KNOWLEDGE_BASE",
    "PAGE_ICONS",
    "MAX_SCORE",
    "MIN_MATURITY_LEVEL",
    "MAX_MATURITY_LEVEL",
]