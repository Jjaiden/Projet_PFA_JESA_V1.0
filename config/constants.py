# constants.py — Structural Constants of the JESA Reference Framework (JDMAF)

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Dict, Tuple


# ============================================================================
# ============================ BACKEND CONSTANTS =============================
# ============================================================================


# ============================================================================
# 1. MATURITY SCALE (BACKEND)
# ============================================================================

SCORE_MIN = 0
SCORE_MAX = 5

VALID_INDICATOR_SCORES = tuple(
    range(SCORE_MIN, SCORE_MAX + 1)
)


MATURITY_LEVELS = {
    0: "Absence",
    1: "Digitization",
    2: "Connectivity",
    3: "Visibility",
    4: "Control & Optimization",
    5: "Supervised Digital Excellence",
}


MATURITY_LEVEL_DESCRIPTIONS = {
    0: (
        "No digital initiative has been identified. "
        "Processes are entirely manual or analog."
    ),
    1: (
        "Digital tools are deployed selectively to replace "
        "certain manual tasks. Solutions remain local, poorly "
        "standardized, and operate independently."
    ),
    2: (
        "Industrial and information technology systems (OT/IT) "
        "are interconnected and exchange data reliably through "
        "standardized interfaces or protocols."
    ),
    3: (
        "Data is centralized, historized, and accessible in real time. "
        "Dashboards and performance indicators support daily "
        "operational management."
    ),
    4: (
        "Data is leveraged to analyze performance, identify the root "
        "causes of deviations, and implement improvement actions."
    ),
    5: (
        "Systems support or automate decision-making through advanced "
        "analytics and artificial intelligence (AI)."
    ),
}


# ============================================================================
# 2. REFERENCE FRAMEWORK HIERARCHY (BACKEND)
# ============================================================================
#
# Structure:
# 5 Pillars → 10 Dimensions → 20 Sub-dimensions → 60 Indicators
# ============================================================================


# ----------------------------------------------------------------------------
# 2.1 Pillars
# ----------------------------------------------------------------------------

PILLARS = {
    "P1": "Digital Infrastructure",
    "P2": "Digital Operations",
    "P3": "Data & Intelligence",
    "P4": "Governance & Cybersecurity",
    "P5": "Human Capital & Skills",
}

PILLAR_IDS = list(PILLARS.keys())


# ----------------------------------------------------------------------------
# 2.2 Dimensions
# ----------------------------------------------------------------------------
# DIMENSION_ID -> (PILLAR_ID, DIMENSION_NAME)
# ----------------------------------------------------------------------------

DIMENSIONS = {
    "D1": ("P1", "OT/IT Infrastructure"),
    "D2": ("P1", "Connectivity & Networks"),
    "D3": ("P2", "Automation & Control"),
    "D4": ("P2", "Supervision & Monitoring"),
    "D5": ("P3", "Data Management"),
    "D6": ("P3", "Analytics & Artificial Intelligence"),
    "D7": ("P4", "OT/IT Cybersecurity"),
    "D8": ("P4", "Digital Governance"),
    "D9": ("P5", "Skills & Training"),
    "D10": ("P5", "Digital Culture & Organization"),
}

DIMENSION_IDS = list(DIMENSIONS.keys())


# Mapping Dimension → Pillar
DIMENSION_TO_PILLAR = {
    dimension_id: pillar_id
    for dimension_id, (pillar_id, _) in DIMENSIONS.items()
}


# Mapping Pillar → Dimensions
PILLAR_TO_DIMENSIONS = {
    pillar_id: [
        dimension_id
        for dimension_id, (dim_pillar_id, _) in DIMENSIONS.items()
        if dim_pillar_id == pillar_id
    ]
    for pillar_id in PILLARS
}


# ----------------------------------------------------------------------------
# 2.3 Sub-dimensions
# ----------------------------------------------------------------------------
# SUBDIMENSION_ID -> (DIMENSION_ID, SUBDIMENSION_NAME)
# ----------------------------------------------------------------------------

SUBDIMENSIONS = {
    "SD1.1": ("D1", "OT Network & Availability"),
    "SD1.2": ("D1", "Servers & Virtualization"),

    "SD2.1": ("D2", "Protocols & Interoperability"),
    "SD2.2": ("D2", "OT/IT Integration"),

    "SD3.1": ("D3", "Automation & Control (DCS/PLC)"),
    "SD3.2": ("D3", "Manufacturing Execution System (MES) & Scheduling"),

    "SD4.1": ("D4", "Acquisition & Control (SCADA) & Operator Interface (HMI)"),
    "SD4.2": ("D4", "Predictive Maintenance"),

    "SD5.1": ("D5", "Historian & Traceability"),
    "SD5.2": ("D5", "Quality & Data Governance"),

    "SD6.1": ("D6", "Analytics & Reporting"),
    "SD6.2": ("D6", "Artificial Intelligence (AI) & Modeling"),

    "SD7.1": ("D7", "Perimeter Security & Segmentation"),
    "SD7.2": ("D7", "Access Management & Authentication"),

    "SD8.1": ("D8", "Policies & Digital Processes"),
    "SD8.2": ("D8", "Compliance & Audit"),

    "SD9.1": ("D9", "Digital Skills Levels"),
    "SD9.2": ("D9", "Training & Development Plans"),

    "SD10.1": ("D10", "Digital Tool Adoption"),
    "SD10.2": ("D10", "Innovation & Continuous Improvement"),
}

SUBDIMENSION_IDS = list(SUBDIMENSIONS.keys())


# Mapping Sub-dimension → Dimension
SUBDIMENSION_TO_DIMENSION = {
    subdimension_id: dimension_id
    for subdimension_id, (dimension_id, _) in SUBDIMENSIONS.items()
}


# Mapping Dimension → Sub-dimensions
DIMENSION_TO_SUBDIMENSIONS = {
    dimension_id: [
        subdimension_id
        for subdimension_id, (sub_dim_id, _) in SUBDIMENSIONS.items()
        if sub_dim_id == dimension_id
    ]
    for dimension_id in DIMENSIONS
}


# ----------------------------------------------------------------------------
# 2.4 Indicator Structure
# ----------------------------------------------------------------------------

INDICATORS_PER_SUBDIMENSION = 3

EXPECTED_INDICATOR_COUNT = (
    len(SUBDIMENSIONS) * INDICATORS_PER_SUBDIMENSION
)


# ============================================================================
# 3. SCORING RULES (BACKEND)
# ============================================================================

APPLICABILITY_APPLICABLE = "Applicable"
APPLICABILITY_NOT_APPLICABLE = "Not Applicable"

VALID_APPLICABILITY_VALUES = (
    APPLICABILITY_APPLICABLE,
    APPLICABILITY_NOT_APPLICABLE,
)

WEIGHT_SUM_TOLERANCE = 0.001


# ============================================================================
# 4. DEFAULT WEIGHTS (BACKEND)
# ============================================================================

DEFAULT_WEIGHT_PILLAR = 1 / len(PILLARS)
DEFAULT_WEIGHT_DIMENSION_PER_PILLAR = 0.5
DEFAULT_WEIGHT_SUBDIMENSION_PER_DIMENSION = 0.5


# ============================================================================
# 5. AGGREGATION AND DMI (BACKEND)
# ============================================================================

DMI_SCALE_FACTOR = 20


# ============================================================================
# 6. MATURITY CALCULATION RULES (BACKEND)
# ============================================================================

WEAKNESS_CAP_INCREMENT = 1
FULL_SATISFACTION_REQUIRED = True


# ============================================================================
# 7. MATURITY BANDS (BACKEND)
# ============================================================================

MATURITY_BANDS = {
    "0-1": (0, 1),
    "2-3": (2, 3),
    "4-5": (4, 5),
}

MATURITY_BAND_NAMES = {
    "0-1": "Foundations",
    "2-3": "Integration",
    "4-5": "Optimization",
}


def get_maturity_band(level: int) -> str:
    """
    Return the maturity band corresponding to a maturity level.

    Args:
        level: Maturity level between 0 and 5.

    Returns:
        '0-1', '2-3', or '4-5'.

    Raises:
        ValueError: If the level is outside [0, 5].
    """

    if level < SCORE_MIN or level > SCORE_MAX:
        raise ValueError(
            f"The maturity level must be between "
            f"{SCORE_MIN} and {SCORE_MAX}. Received: {level}"
        )

    if level <= 1:
        return "0-1"

    if level <= 3:
        return "2-3"

    return "4-5"


# ============================================================================
# 8. HIERARCHY LEVELS (BACKEND)
# ============================================================================

class HierarchyLevel:
    INDICATOR = "indicator"
    SUBDIMENSION = "subdimension"
    DIMENSION = "dimension"
    PILLAR = "pillar"
    DMI = "dmi"


HIERARCHY_LEVELS = (
    HierarchyLevel.INDICATOR,
    HierarchyLevel.SUBDIMENSION,
    HierarchyLevel.DIMENSION,
    HierarchyLevel.PILLAR,
    HierarchyLevel.DMI,
)


# ============================================================================
# 9. ENTITY TYPES (BACKEND)
# ============================================================================

ENTITY_TYPES = {
    "indicator": "Indicator",
    "subdimension": "Sub-dimension",
    "dimension": "Dimension",
    "pillar": "Pillar",
    "dmi": "DMI",
}


# ============================================================================
# 10. DECISION ENGINE — TPI (BACKEND)
# ============================================================================

TPI_PARAMETERS_FAVORABLE = (
    "gap",
    "business_impact",
    "strategic_importance",
    "expected_roi",
)

TPI_PARAMETERS_INVERTED = (
    "implementation_cost",
    "implementation_difficulty",
)

TPI_ALL_PARAMETERS = (
    TPI_PARAMETERS_FAVORABLE
    + TPI_PARAMETERS_INVERTED
)

DEFAULT_TPI_WEIGHT = 1 / len(TPI_ALL_PARAMETERS)

TPI_PRIORITY_THRESHOLDS = [
    (0.80, 1.00, "Critical", "Phase 1 (< 6 months)"),
    (0.60, 0.80, "High", "Phase 1-2 (6-12 months)"),
    (0.40, 0.60, "Medium", "Phase 2 (12-24 months)"),
    (0.20, 0.40, "Low", "Long term, depending on resources"),
    (0.00, 0.20, "Very Low", "Not a priority, to be reassessed"),
]


# ============================================================================
# 11. GAP THRESHOLDS (BACKEND)
# ============================================================================

GAP_THRESHOLDS = {
    "critical": 2.0,
    "high": 1.5,
    "medium": 1.0,
    "low": 0.5,
}


# ============================================================================
# 12. REFERENCE EXCEL SHEET NAMES (BACKEND)
# ============================================================================

class RefSheets:
    README = "README"
    ASSESSMENT_METADATA = "ASSESSMENT_METADATA"
    HIERARCHY = "HIERARCHY"
    GENERIC_MATURITY_SCALE = "GENERIC_MATURITY_SCALE"
    DIMENSION_MATURITY_MATRICES = "DIMENSION_MATURITY_MATRICES"
    TARGET_LEVELS = "TARGET_LEVELS"
    WEIGHTS_CONFIGURATION = "WEIGHTS_CONFIGURATION"
    INDICATORS = "INDICATORS"
    INDICATOR_SCORING_GRIDS = "INDICATOR_SCORING_GRIDS"
    EVIDENCE_CATALOG = "EVIDENCE_CATALOG"
    QUESTIONNAIRE_TEMPLATE = "QUESTIONNAIRE_TEMPLATE"
    CALCULATION_RULES = "CALCULATION_RULES"
    QUALITY_CONTROL = "QUALITY_CONTROL"


REFERENTIEL_SHEETS = [
    RefSheets.README,
    RefSheets.ASSESSMENT_METADATA,
    RefSheets.HIERARCHY,
    RefSheets.GENERIC_MATURITY_SCALE,
    RefSheets.DIMENSION_MATURITY_MATRICES,
    RefSheets.TARGET_LEVELS,
    RefSheets.WEIGHTS_CONFIGURATION,
    RefSheets.INDICATORS,
    RefSheets.INDICATOR_SCORING_GRIDS,
    RefSheets.EVIDENCE_CATALOG,
    RefSheets.QUESTIONNAIRE_TEMPLATE,
    RefSheets.CALCULATION_RULES,
    RefSheets.QUALITY_CONTROL,
]


# ============================================================================
# 13. KNOWLEDGE BASE SHEET NAMES (BACKEND)
# ============================================================================

class KnowledgeBaseSheets:
    README = "README"
    KNOWLEDGE_TAXONOMY = "KNOWLEDGE_TAXONOMY"
    RECOMMENDATIONS = "RECOMMENDATIONS"
    EFFORT_SCALE = "EFFORT_SCALE"
    HORIZON_SCALE = "HORIZON_SCALE"
    RECOMMENDATION_STEPS = "RECOMMENDATION_STEPS"
    TRIGGER_MAPPING = "TRIGGER_MAPPING"
    DEPENDENCIES = "DEPENDENCIES"
    COMPLETION_EVIDENCE = "COMPLETION_EVIDENCE"
    BEST_PRACTICES = "BEST_PRACTICES"
    TECHNOLOGY_CAPABILITIES = "TECHNOLOGY_CAPABILITIES"
    DECISION_INPUT_GUIDE = "DECISION_INPUT_GUIDE"
    DECISION_INPUT_SCHEMA = "DECISION_INPUT_SCHEMA"
    ROADMAP_RULES = "ROADMAP_RULES"
    TRACEABILITY = "TRACEABILITY"
    QUALITY_CONTROL = "QUALITY_CONTROL"


KNOWLEDGE_BASE_SHEETS = [
    KnowledgeBaseSheets.README,
    KnowledgeBaseSheets.KNOWLEDGE_TAXONOMY,
    KnowledgeBaseSheets.RECOMMENDATIONS,
    KnowledgeBaseSheets.EFFORT_SCALE,
    KnowledgeBaseSheets.HORIZON_SCALE,
    KnowledgeBaseSheets.RECOMMENDATION_STEPS,
    KnowledgeBaseSheets.TRIGGER_MAPPING,
    KnowledgeBaseSheets.DEPENDENCIES,
    KnowledgeBaseSheets.COMPLETION_EVIDENCE,
    KnowledgeBaseSheets.BEST_PRACTICES,
    KnowledgeBaseSheets.TECHNOLOGY_CAPABILITIES,
    KnowledgeBaseSheets.DECISION_INPUT_GUIDE,
    KnowledgeBaseSheets.DECISION_INPUT_SCHEMA,
    KnowledgeBaseSheets.ROADMAP_RULES,
    KnowledgeBaseSheets.TRACEABILITY,
    KnowledgeBaseSheets.QUALITY_CONTROL,
]


# ============================================================================
# 14. BACKEND ERROR MESSAGES
# ============================================================================

ERROR_MESSAGES = {
    "invalid_score": "The score must be an integer between 0 and 5.",
    "invalid_indicator_id": "Invalid indicator ID format.",
    "invalid_dimension": "Invalid dimension ID: {dim_id}",
    "invalid_subdimension": "Invalid subdimension ID: {subdimension_id}",
    "invalid_pillar": "Invalid pillar ID: {pillar_id}",
    "invalid_applicability": "Invalid applicability status: {value}",
    "weight_sum_error": "The sum of weights must be equal to 1.0. Received: {sum}",
    "data_validation_error": "Data validation error: {error}",
    "file_not_found": "File not found: {path}",
    "sheet_not_found": "Sheet '{sheet}' not found in file {file}",
    "assessment_not_found": "Assessment not found for ID: {assessment_id}",
}


# ============================================================================
# 15. REFERENCE FRAMEWORK VALIDATION CONSTANTS (BACKEND)
# ============================================================================

EXPECTED_PILLAR_COUNT = 5
EXPECTED_DIMENSION_COUNT = 10
EXPECTED_SUBDIMENSION_COUNT = 20
DIMENSIONS_PER_PILLAR = 2
SUBDIMENSIONS_PER_DIMENSION = 2


# ============================================================================
# ============================ FRONTEND CONSTANTS ============================
# ============================================================================


# ============================================================================
# 16. APPLICATION (FRONTEND)
# ============================================================================

@dataclass(frozen=True)
class AppInfo:
    """Static information about the application."""

    NAME: str = "JESA Digital Maturity Assessment Tool"
    ACRONYM: str = "JESA DMAT"
    VERSION: str = "1.0.0"


APP = AppInfo()


# ============================================================================
# 17. NAVIGATION (FRONTEND)
# ============================================================================

class Page(Enum):
    """Main pages with title, icon, and display order."""

    HOME = ("Home", "🏠", 0)
    NEW_ASSESSMENT = ("New Assessment", "📝", 1)
    DASHBOARD = ("Dashboard", "📊", 2)
    GAP_ANALYSIS = ("Gap Analysis", "🔍", 3)
    RECOMMENDATIONS = ("Recommendations", "💡", 4)
    DECISION_ANALYSIS = ("Decision Analysis", "⚖️", 5)
    ROADMAP = ("Roadmap", "🗺️", 6)
    EXPORT = ("Export", "📤", 7)

    def __init__(self, title: str, icon: str, order: int):
        self.title = title
        self.icon = icon
        self.order = order

    @classmethod
    def ordered_pages(cls) -> Tuple["Page", ...]:
        """Return the pages sorted by their display order."""

        return tuple(sorted(cls, key=lambda p: p.order))


# ============================================================================
# 18. MATURITY LEVELS (FRONTEND - UI ONLY)
# ============================================================================

class MaturityLevel(IntEnum):
    """Digital maturity levels (0 to 5)."""

    LEVEL_0 = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5


# ============================================================================
# 19. PILLARS (FRONTEND - UI ONLY)
# ============================================================================

class Pillar(str, Enum):
    """Fundamental pillars of the maturity assessment (for UI)."""

    INFRASTRUCTURE = "Infrastructure & Connectivity"
    OPERATIONS = "Digital Operations"
    DATA_AI = "Data & Artificial Intelligence"
    GOVERNANCE = "Governance & Cybersecurity"
    HUMAN_CAPITAL = "Human Capital & Skills"


NUMBER_OF_PILLARS: int = len(Pillar)


# ============================================================================
# 20. PRIORITY LABELS (FRONTEND)
# ============================================================================

class Priority(str, Enum):
    """Priority levels for recommendations and actions."""

    VERY_HIGH = "Very High"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    VERY_LOW = "Very Low"


# ============================================================================
# 21. STATUS (FRONTEND)
# ============================================================================

class Status(str, Enum):
    """States used in the interface (alerts, badges, etc.)."""

    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


# ============================================================================
# 22. ALLOWED EXTENSIONS & EXPORT (FRONTEND)
# ============================================================================

ALLOWED_EXTENSIONS: Tuple[str, ...] = ("xlsx", "csv", "pdf")
"""Allowed file extensions for imports/exports."""


class ExportFormat(str, Enum):
    """Supported export formats."""

    PDF = "PDF"
    EXCEL = "Excel"


SHEET_ASSESSMENT = "Assessment"
SHEET_KNOWLEDGE_BASE = "Knowledge Base"


PAGE_ICONS: Dict[str, str] = {
    page.name: page.icon
    for page in Page
}


MAX_SCORE: float = 100.0
"""Maximum theoretical score (in percentage)."""


MIN_MATURITY_LEVEL: MaturityLevel = MaturityLevel.LEVEL_0
MAX_MATURITY_LEVEL: MaturityLevel = MaturityLevel.LEVEL_5