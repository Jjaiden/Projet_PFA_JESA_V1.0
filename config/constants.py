"""
constants.py — Constantes structurelles du référentiel JESA (JDMAF)

Ce module contient les constantes nécessaires au BACKEND (moteurs de calcul, 
loader, validation) ainsi que les constantes pour le FRONTEND (navigation, UI).

BACKEND (Sections 1–6, 10–15):
- Échelle de maturité 0-5
- Hiérarchie Pilier → Dimension → Sous-dimension → Indicateur
- Règles de notation et d'agrégation
- Paramètres du DMI et du TPI
- Noms des feuilles Excel (loader/validation)
- Messages d'erreur backend

FRONTEND (Sections 7–9, 16–22):
- Navigation (pages, icônes, ordre)
- Enums pour l'UI (priorités, statuts, formats)
- Configuration des extensions autorisées

Les données détaillées du référentiel (60 indicateurs, grilles de scoring, etc.)
sont chargées depuis les fichiers Excel par loader.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Dict, Tuple

# ============================================================================
# ============================ BACKEND CONSTANTS =============================
# ============================================================================


# ============================================================================
# 1. ÉCHELLE DE MATURITÉ (BACKEND)
# ============================================================================

SCORE_MIN = 0
SCORE_MAX = 5

VALID_INDICATOR_SCORES = tuple(
    range(SCORE_MIN, SCORE_MAX + 1)
)

MATURITY_LEVELS = {
    0: "Absence",
    1: "Informatisation",
    2: "Connectivité",
    3: "Visibilité",
    4: "Maîtrise & Optimisation",
    5: "Excellence digitale supervisée",
}

MATURITY_LEVEL_DESCRIPTIONS = {
    0: (
        "Aucune initiative digitale identifiée. "
        "Les processus sont entièrement manuels ou analogiques."
    ),
    1: (
        "Des outils numériques sont déployés ponctuellement pour remplacer "
        "certaines tâches manuelles. Les solutions restent locales, peu "
        "standardisées et fonctionnent indépendamment."
    ),
    2: (
        "Les systèmes industriels et informatiques (OT/IT) sont "
        "interconnectés et échangent des données de manière fiable via "
        "des interfaces ou des protocoles normalisés."
    ),
    3: (
        "Les données sont centralisées, historisées et accessibles en "
        "temps réel. Des tableaux de bord et des indicateurs de performance "
        "soutiennent le pilotage quotidien des opérations."
    ),
    4: (
        "Les données sont exploitées pour analyser les performances, "
        "identifier les causes des écarts et mettre en œuvre des actions "
        "d'amélioration."
    ),
    5: (
        "Les systèmes assistent ou automatisent la prise de décision "
        "grâce à des analyses avancées et à l'intelligence artificielle (IA)."
    ),
}


# ============================================================================
# 2. HIÉRARCHIE DU RÉFÉRENTIEL (BACKEND)
# ============================================================================
#
# Structure :
# 5 Piliers → 10 Dimensions → 20 Sous-dimensions → 60 Indicateurs
# ============================================================================


# ----------------------------------------------------------------------------
# 2.1 Piliers
# ----------------------------------------------------------------------------

PILLARS = {
    "P1": "Infrastructure numérique",
    "P2": "Opérations digitales",
    "P3": "Données & Intelligence",
    "P4": "Gouvernance & Cybersécurité",
    "P5": "Capital humain & Compétences",
}

PILLAR_IDS = list(PILLARS.keys())


# ----------------------------------------------------------------------------
# 2.2 Dimensions
# ----------------------------------------------------------------------------
# DIMENSION_ID -> (PILLAR_ID, DIMENSION_NAME)
# ----------------------------------------------------------------------------

DIMENSIONS = {
    "D1": ("P1", "Infrastructure OT/IT"),
    "D2": ("P1", "Connectivité & Réseaux"),
    "D3": ("P2", "Automatisation & Contrôle"),
    "D4": ("P2", "Supervision & Monitoring"),
    "D5": ("P3", "Gestion des données"),
    "D6": ("P3", "Analyse & Intelligence Artificielle"),
    "D7": ("P4", "Cybersécurité OT/IT"),
    "D8": ("P4", "Gouvernance numérique"),
    "D9": ("P5", "Compétences & Formation"),
    "D10": ("P5", "Culture digitale & Organisation"),
}

DIMENSION_IDS = list(DIMENSIONS.keys())


# Mapping Dimension → Pilier
DIMENSION_TO_PILLAR = {
    dimension_id: pillar_id
    for dimension_id, (pillar_id, _) in DIMENSIONS.items()
}

# Mapping Pilier → Dimensions
PILLAR_TO_DIMENSIONS = {
    pillar_id: [
        dimension_id
        for dimension_id, (dim_pillar_id, _) in DIMENSIONS.items()
        if dim_pillar_id == pillar_id
    ]
    for pillar_id in PILLARS
}


# ----------------------------------------------------------------------------
# 2.3 Sous-dimensions
# ----------------------------------------------------------------------------
# SUBDIMENSION_ID -> (DIMENSION_ID, SUBDIMENSION_NAME)
# ----------------------------------------------------------------------------

SUBDIMENSIONS = {
    "SD1.1": ("D1", "Réseau OT & Disponibilité"),
    "SD1.2": ("D1", "Serveurs & Virtualisation"),
    "SD2.1": ("D2", "Protocoles & Interopérabilité"),
    "SD2.2": ("D2", "Intégration OT/IT"),
    "SD3.1": ("D3", "Automates & Contrôle (DCS/PLC)"),
    "SD3.2": ("D3", "Système d'Exécution de la Fabrication (MES) & Ordonnancement"),
    "SD4.1": ("D4", "Acquisition & Contrôle (SCADA) & Interface Opérateur (HMI)"),
    "SD4.2": ("D4", "Maintenance prédictive"),
    "SD5.1": ("D5", "Historian & Traçabilité"),
    "SD5.2": ("D5", "Qualité & Gouvernance des données"),
    "SD6.1": ("D6", "Analytique & Reporting"),
    "SD6.2": ("D6", "Intelligence Artificielle (IA) & Modélisation"),
    "SD7.1": ("D7", "Sécurité périmétrique & Segmentation"),
    "SD7.2": ("D7", "Gestion des accès & Authentification"),
    "SD8.1": ("D8", "Politiques & Processus digitaux"),
    "SD8.2": ("D8", "Conformité & Audit"),
    "SD9.1": ("D9", "Niveaux de compétences digitales"),
    "SD9.2": ("D9", "Plans de formation & Développement"),
    "SD10.1": ("D10", "Adoption des outils numériques"),
    "SD10.2": ("D10", "Innovation & Amélioration continue"),
}

SUBDIMENSION_IDS = list(SUBDIMENSIONS.keys())


# Mapping Sous-dimension → Dimension
SUBDIMENSION_TO_DIMENSION = {
    subdimension_id: dimension_id
    for subdimension_id, (dimension_id, _) in SUBDIMENSIONS.items()
}

# Mapping Dimension → Sous-dimensions
DIMENSION_TO_SUBDIMENSIONS = {
    dimension_id: [
        subdimension_id
        for subdimension_id, (sub_dim_id, _) in SUBDIMENSIONS.items()
        if sub_dim_id == dimension_id
    ]
    for dimension_id in DIMENSIONS
}


# ----------------------------------------------------------------------------
# 2.4 Structure des indicateurs
# ----------------------------------------------------------------------------

INDICATORS_PER_SUBDIMENSION = 3

EXPECTED_INDICATOR_COUNT = (
    len(SUBDIMENSIONS) * INDICATORS_PER_SUBDIMENSION
)


# ============================================================================
# 3. RÈGLES DE NOTATION (BACKEND)
# ============================================================================

APPLICABILITY_APPLICABLE = "Applicable"
APPLICABILITY_NOT_APPLICABLE = "Non applicable"

VALID_APPLICABILITY_VALUES = (
    APPLICABILITY_APPLICABLE,
    APPLICABILITY_NOT_APPLICABLE,
)

WEIGHT_SUM_TOLERANCE = 0.001


# ============================================================================
# 4. PONDÉRATIONS PAR DÉFAUT (BACKEND)
# ============================================================================

DEFAULT_WEIGHT_PILLAR = 1 / len(PILLARS)
DEFAULT_WEIGHT_DIMENSION_PER_PILLAR = 0.5
DEFAULT_WEIGHT_SUBDIMENSION_PER_DIMENSION = 0.5


# ============================================================================
# 5. AGRÉGATION ET DMI (BACKEND)
# ============================================================================

DMI_SCALE_FACTOR = 20


# ============================================================================
# 6. RÈGLES DE CALCUL DE MATURITÉ (BACKEND)
# ============================================================================

WEAKNESS_CAP_INCREMENT = 1
FULL_SATISFACTION_REQUIRED = True


# ============================================================================
# 7. BANDES DE MATURITÉ (BACKEND)
# ============================================================================

MATURITY_BANDS = {
    "0-1": (0, 1),
    "2-3": (2, 3),
    "4-5": (4, 5),
}

MATURITY_BAND_NAMES = {
    "0-1": "Fondations",
    "2-3": "Intégration",
    "4-5": "Optimisation",
}


def get_maturity_band(level: int) -> str:
    """
    Retourne la bande de maturité correspondant à un niveau.

    Args:
        level: Niveau de maturité compris entre 0 et 5.

    Returns:
        '0-1', '2-3' ou '4-5'.

    Raises:
        ValueError: si le niveau est hors de [0, 5].
    """
    if level < SCORE_MIN or level > SCORE_MAX:
        raise ValueError(
            f"Le niveau de maturité doit être compris entre "
            f"{SCORE_MIN} et {SCORE_MAX}. Reçu : {level}"
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
# 9. TYPES D'ENTITÉS (BACKEND)
# ============================================================================

ENTITY_TYPES = {
    "indicator": "Indicateur",
    "subdimension": "Sous-dimension",
    "dimension": "Dimension",
    "pillar": "Pilier",
    "dmi": "DMI",
}


# ============================================================================
# 10. MOTEUR DÉCISIONNEL — TPI (BACKEND)
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
    (0.80, 1.00, "Critique", "Phase 1 (< 6 mois)"),
    (0.60, 0.80, "Haute", "Phase 1-2 (6-12 mois)"),
    (0.40, 0.60, "Moyenne", "Phase 2 (12-24 mois)"),
    (0.20, 0.40, "Faible", "Long terme, selon ressources"),
    (0.00, 0.20, "Très faible", "Non prioritaire, à réévaluer"),
]


# ============================================================================
# 11. SEUILS DE GAP (BACKEND)
# ============================================================================

GAP_THRESHOLDS = {
    "critical": 2.0,
    "high": 1.5,
    "medium": 1.0,
    "low": 0.5,
}


# ============================================================================
# 12. NOMS DES FEUILLES DU RÉFÉRENTIEL EXCEL (BACKEND)
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
# 13. NOMS DES FEUILLES DE LA BASE DE CONNAISSANCES (BACKEND)
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
# 14. MESSAGES D'ERREUR BACKEND
# ============================================================================

ERROR_MESSAGES = {
    "invalid_score": "Le score doit être un entier entre 0 et 5.",
    "invalid_indicator_id": "Format d'ID d'indicateur invalide.",
    "invalid_dimension": "ID de dimension invalide : {dim_id}",
    "invalid_subdimension": "ID de sous-dimension invalide : {subdimension_id}",
    "invalid_pillar": "ID de pilier invalide : {pillar_id}",
    "invalid_applicability": "Statut d'applicabilité invalide : {value}",
    "weight_sum_error": "La somme des poids doit être égale à 1.0. Reçu : {sum}",
    "data_validation_error": "Erreur de validation des données : {error}",
    "file_not_found": "Fichier non trouvé : {path}",
    "sheet_not_found": "Feuille '{sheet}' non trouvée dans le fichier {file}",
    "assessment_not_found": "Évaluation non trouvée pour l'ID : {assessment_id}",
}


# ============================================================================
# 15. CONSTANTES DE VALIDATION DU RÉFÉRENTIEL (BACKEND)
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
    """Informations statiques sur l'application."""
    NAME: str = "JESA Digital Maturity Assessment Tool"
    ACRONYM: str = "JESA DMAT"
    VERSION: str = "1.0.0"

APP = AppInfo()


# ============================================================================
# 17. NAVIGATION (FRONTEND)
# ============================================================================

class Page(Enum):
    """Pages principales avec titre, icône et ordre d'affichage."""
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
    def ordered_pages(cls) -> Tuple[Page, ...]:
        """Retourne les pages triées selon leur ordre d'affichage."""
        return tuple(sorted(cls, key=lambda p: p.order))


# ============================================================================
# 18. MATURITY LEVELS (FRONTEND - UI ONLY)
# ============================================================================

class MaturityLevel(IntEnum):
    """Niveaux de maturité digitale (0 à 5)."""
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
    """Piliers fondamentaux de l'évaluation de maturité (pour l'UI)."""
    INFRASTRUCTURE = "Infrastructure & Connectivité"
    OPERATIONS = "Opérations Digitales"
    DATA_AI = "Données & Intelligence Artificielle"
    GOVERNANCE = "Gouvernance & Cybersécurité"
    HUMAN_CAPITAL = "Capital Humain & Compétences"

NUMBER_OF_PILLARS: int = len(Pillar)


# ============================================================================
# 20. PRIORITY LABELS (FRONTEND)
# ============================================================================

class Priority(str, Enum):
    """Niveaux de priorité pour les recommandations et actions."""
    VERY_HIGH = "Very High"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    VERY_LOW = "Very Low"


# ============================================================================
# 21. STATUS (FRONTEND)
# ============================================================================

class Status(str, Enum):
    """États utilisés dans l'interface (alertes, badges, etc.)."""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


# ============================================================================
# 22. EXTENSIONS AUTORISÉES & EXPORT (FRONTEND)
# ============================================================================

ALLOWED_EXTENSIONS: Tuple[str, ...] = ("xlsx", "csv", "pdf")
"""Extensions de fichiers autorisées pour les imports/exports."""

class ExportFormat(str, Enum):
    """Formats supportés pour les exports."""
    PDF = "PDF"
    EXCEL = "Excel"

SHEET_ASSESSMENT = "Assessment"
SHEET_KNOWLEDGE_BASE = "Knowledge Base"

PAGE_ICONS: Dict[str, str] = {page.name: page.icon for page in Page}

MAX_SCORE: float = 100.0
"""Score maximal théorique (en pourcentage)."""

MIN_MATURITY_LEVEL: MaturityLevel = MaturityLevel.LEVEL_0
MAX_MATURITY_LEVEL: MaturityLevel = MaturityLevel.LEVEL_5


# ============================================================================
# FIN DU MODULE
# ============================================================================